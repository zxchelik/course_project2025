from datetime import date
from typing import List

from pydantic import BaseModel, validator
from sqlalchemy import select, update, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.database.models.blank_cassettes import BlankCassettes, CassetteType
from src.backend.database.session_context import async_session_context


class TaskModel(BaseModel):
    id: int
    cassette_name: str
    quantity: int
    is_completed: bool
    type: str
    priority: int
    customer_id: int
    worker_id: int | None
    technical_comment: str
    comment: str | None

    def to_list_for_excel(self):
        return [
            self.id,
            self.cassette_name,
            self.type,
            self.quantity,
            None,
            self.priority,
            None,
            self.technical_comment,
            self.comment,
        ]

    def to_str_table_view(self):
        info = [
            ("Наимен.", self.cassette_name),
            ("Кол-во", self.quantity),
            ("Приор.", self.priority),
            ("Тип", self.type),
        ]
        output = ""
        pattern = "{key:<7}:{value:<17}\n"
        for key, value in info:
            output += pattern.format(key=key, value=value)

        key, value = "Т. ком.", self.technical_comment
        output += pattern.format(key=key, value=value)
        if self.comment:
            key, value = "Ком.", self.comment
            output += pattern.format(key=key, value=value)
        return output

    @validator("type")
    def validate_type(cls, value):
        types = CassetteType.to_list()
        if value in types:
            return value
        raise ValueError(f"Invalid state: {value}, but it should be in {types}")

    class Config:
        orm_mode = True


class AddTaskModel(BaseModel):
    cassette_name: str
    quantity: int
    priority: int
    type: str
    technical_comment: str
    comment: str | None


class EditTaskModel(BaseModel):
    id: int
    new_quantity: int | None
    new_priority: int | None

    def to_dict(self) -> dict:
        d = {"id": int(self.id)}
        if self.new_quantity is not None:
            d["quantity"] = self.new_quantity
        if self.new_priority is not None:
            d["priority"] = self.new_priority
        return d


class DeleteTaskModel(BaseModel):
    id: int


@async_session_context
async def add_tasks(session: AsyncSession, tasks: List[AddTaskModel], customer_id: int) -> None:
    blank_cassettes = []
    for task in tasks:
        blank_cassettes.append(BlankCassettes(**task.dict(), customer_id=customer_id))

    session.add_all(blank_cassettes)
    await session.commit()


@async_session_context
async def edit_tasks(
    session: AsyncSession, task_updates: List[EditTaskModel], task_deletes: List[DeleteTaskModel] | None
) -> None:
    update_mappings = [i.to_dict() for i in task_updates]
    await session.execute(update(BlankCassettes), update_mappings)
    if task_deletes:
        await session.execute(delete(BlankCassettes).where(BlankCassettes.id.in_([i.id for i in task_deletes])))


@async_session_context
async def get_tasks(session: AsyncSession, from_id: int = 0, to_id: int | None = None) -> List[TaskModel]:
    stmt = select(BlankCassettes).where(BlankCassettes.is_completed == False).order_by(desc(BlankCassettes.priority))
    result = (await session.execute(stmt)).scalars().all()
    if not to_id:
        to_id = len(result)
    return [TaskModel.from_orm(i) for i in result[from_id : to_id + 1]]


@async_session_context
async def get_task_by_id(session: AsyncSession, task_id: int) -> TaskModel:
    task = await session.get(BlankCassettes, task_id)
    return TaskModel.from_orm(task)


@async_session_context
async def execute_task(session: AsyncSession, task_id: int, quantity: int, worker_id: int, cut_date: date) -> None:
    task = await session.get(BlankCassettes, task_id)

    if quantity < task.quantity:
        # noinspection PyTypeChecker
        session.add(
            BlankCassettes(
                cassette_name=task.cassette_name,
                quantity=quantity,
                is_completed=True,
                priority=task.priority,
                customer_id=task.customer_id,
                worker_id=worker_id,
                technical_comment=task.technical_comment,
                comment=task.comment,
                type=task.type,
            )
        )
        task.quantity -= quantity
    else:
        task.quantity = quantity
        task.worker_id = worker_id
        task.is_completed = True

    from src.backend.database.db_cmd.cassette_cmd import add_cassette

    await add_cassette(
        quantity=quantity,
        priority=task.priority,
        name=task.cassette_name,
        type=task.type,
        cut_date=cut_date,
        cutter_id=worker_id,
        technical_comment=task.technical_comment,
        comment=task.comment,
    )

    await session.commit()
