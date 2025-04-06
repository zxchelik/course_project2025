from datetime import date
from typing import Sequence

from sqlalchemy import extract
from sqlalchemy import select, not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.database.db_cmd.groups_cmd import create_group
from src.backend.database.models.container import Container
from src.backend.database.models.storage_movements import StorageMovements
from src.backend.database.session_context import async_session_context


@async_session_context
async def add_container(
    session: AsyncSession,
    number,
    date_cont,
    name,
    color,
    weight,
    batch_number,
    cover_article,
    comments,
    users_id,
    storage="База",
):
    group, percent = await create_group(users_id=users_id)

    container = Container(
        number=number,
        date_cont=date_cont,
        name=name,
        color=color,
        weight=weight,
        batch_number=batch_number,
        cover_article=cover_article,
        comments=comments,
        percent=percent,
        storage=storage,
    )
    container.group = group
    session.add(container)


@async_session_context
async def select_cont(session: AsyncSession, id: int) -> Container:
    query = select(Container).where(Container.id == id).options(selectinload(Container.group))
    container = await session.execute(query)
    return container.scalars().one()


@async_session_context
async def get_last_cont_numb(session: AsyncSession, furnace, month, year_char) -> int:
    query = select(Container).where(extract("MONTH", Container.date_cont) == month)
    containers = await session.execute(query)
    containers = containers.scalars().all()
    res = 1
    for container in containers:
        numb = str(container.number)
        if numb.startswith(f"{year_char}{furnace}.{month}."):
            n = numb.split(".")[-1]
            if n[-1] in "ABCD":
                n = n[:-1]
            res = max(int(n) + 1, res)
    if res is None:
        res = 1
    return res


@async_session_context
async def check_cont_numb(session: AsyncSession, cont_number: str):
    query = select(Container).where(Container.number == cont_number)
    cont = (await session.scalars(query)).one_or_none()
    if cont is None:
        return True
    else:
        return False


@async_session_context
async def get_all_container_by_month(session: AsyncSession, year, month) -> dict:
    query = (
        select(Container)
        .where(extract("MONTH", Container.date_cont) == month, extract("YEAR", Container.date_cont) == year)
        .options(selectinload(Container.group))
        .where(not_(Container.number.contains("-")))
    )
    cont_list = (await session.scalars(query)).all()
    data = {}

    for cont in cont_list:
        users, info = cont.get_info_for_exel()
        if not any(user.is_admin for user in users):
            for user in users:
                user_info = data.setdefault(user.fio, [])
                user_info.append(info)

    return data


@async_session_context
async def get_stored_containers_from_to(session: AsyncSession, first_date: date, last_date) -> Sequence[Container]:
    query = (
        select(Container)
        .where(Container.date_cont >= first_date)
        .where(Container.date_cont <= last_date)
        .where(not_(Container.number.contains("-")))
        # FIXME:.where(Container.state not in ["defective", "shipped"])
        .order_by(Container.number)
        .options(selectinload(Container.group))
    )
    containers = (await session.scalars(query)).all()
    return containers


@async_session_context
async def move_container_with_session(
    session: AsyncSession, number: str, to_storage: str, user_id: int, reasons_for_moving: str
):
    await move_container(
        session=session, number=number, to_storage=to_storage, user_id=user_id, reasons_for_moving=reasons_for_moving
    )


async def move_container(session: AsyncSession, number: str, to_storage: str, user_id: int, reasons_for_moving: str):
    """
    move a container

    @param session: SQLAlchemy session
    @param number:  Container number
    @param to_storage: Storage name
    """
    stmt = select(Container).where(Container.number == number)
    container = (await session.scalars(stmt)).one_or_none()
    if not container:
        raise ValueError(f"Container {number} not found")
    from_storage = container.storage
    if from_storage == to_storage:
        raise Warning(f"Container is already in this storage unit")
    storage_move = StorageMovements(
        product_number=container.number,
        from_storage=from_storage,
        to_storage=to_storage,
        user_id=user_id,
        reasons_for_moving=reasons_for_moving,
    )
    session.add(storage_move)
    container.storage = to_storage
    await session.commit()


@async_session_context
async def get_container_number_by_suffix_assembling(session: AsyncSession, suffix: int) -> Sequence[str]:
    stmt = await session.execute(
        select(Container.number)
        .filter(not_(Container.number.contains("-")))
        .filter(Container.number.like(f"%{suffix:03d}"))
        .filter(Container.storage != "Отгружено")
        .filter(Container.storage != "Н/Д")
        .filter(~Container.storage.op("~")(r"^[A-Za-zА-Яа-я]\d+\.\d+\.\d+$"))
    )
    return stmt.scalars().all()
