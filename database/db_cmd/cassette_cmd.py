import datetime
from typing import Sequence

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.db_cmd.Exceptions import AdditionNotFoundException
from database.models import Cassette, CassetteGroupMember
from database.models.blank_cassettes import CassetteType
from database.models.cassette import CassetteState
from database.models.cassette_group_member import CassetteGroupMemberType
from database.modelsDTO.cassette import CassetteNQHModel, CassetteNumberModel, RawCassetteModel, \
    WeldCassetteTaskModel
from database.session_context import async_session_context

help_user_percent = 0.5


@async_session_context
async def add_cassette(session: AsyncSession,
                       quantity: int,
                       priority: int,
                       name: str,
                       type: str,
                       cut_date: datetime.date,
                       cutter_id: int,
                       technical_comment: str,
                       comment: str,
                       ):
    session.add_all(
        [Cassette(
            name=name,
            priority=priority,
            type=type,
            cut_date=cut_date,
            cutter_id=cutter_id,
            technical_comment=technical_comment,
            comment=comment,
        ) for _ in range(quantity)]
    )
    await session.commit()


def hash_exp(name, tcomment):
    return func.md5(func.concat(name, '|', tcomment))


@async_session_context
async def get_tasks_for_welding(session: AsyncSession) -> list[CassetteNQHModel]:
    stmt = (
        select(
            Cassette.name,
            func.count(Cassette.id).label("quantity"),
            hash_exp(Cassette.name, Cassette.technical_comment).label("hash")
        )
        .order_by(desc(Cassette.priority))
        .filter(Cassette.state == CassetteState.CUTED)
        .filter(Cassette.type != CassetteType.WELDED)
        .filter(Cassette.in_working == False)
        .group_by(Cassette.name)
        .group_by(Cassette.technical_comment)
        .group_by(Cassette.priority)
    )

    data = (await session.execute(stmt)).all()
    res = []
    for r in data:
        name, quantity, hash_ = r
        res.append(CassetteNQHModel(name=name, quantity=quantity, hash=hash_))
    return res


# @async_session_context
# async def get_tasks_for_welding_by_hash(session: AsyncSession, task_hash: str, quantity: int = 1) -> Union[
#     list[CassetteModel],
#     CassetteModel
# ]:
#     stmt = (
#         select(Cassette)
#         .order_by(Cassette.id)
#         .filter(Cassette.state == CassetteState.CUT)
#         .filter(Cassette.type != CassetteType.WELDED)
#         .filter(Cassette.in_working == False)
#         .filter(
#             hash_exp(Cassette.name, Cassette.technical_comment) == task_hash
#         )
#     )
#
#     if quantity == 1:
#         res = (await session.execute(stmt)).scalars().first()
#         return CassetteModel.from_orm(res)
#
#     res = (await session.execute(stmt)).scalars().all()
#
#     return [CassetteModel.from_orm(i) for i in res[:quantity]]


@async_session_context
async def get_raw_tasks_for_welding_by_hash(session: AsyncSession, task_hash: str) -> RawCassetteModel:
    stmt = (
        select(Cassette)
        .order_by(Cassette.id)
        .filter(Cassette.state == CassetteState.CUTED)
        .filter(Cassette.type != CassetteType.WELDED)
        .filter(Cassette.in_working == False)
        .filter(
            hash_exp(Cassette.name, Cassette.technical_comment) == task_hash
        )
    )

    res = (await session.execute(stmt)).scalars().first()
    return RawCassetteModel.from_orm(res)


@async_session_context
async def get_max_quantity_for_welding_by_hash(session: AsyncSession, task_hash: str):
    q = select(hash_exp(Cassette.name, Cassette.technical_comment).label("hash")).subquery()
    stmt = (
        select(
            func.count(q.c.hash)
        )
        .filter(q.c.hash == task_hash)
        .group_by(q.c.hash)
    )
    return (await session.execute(stmt)).scalars().first()


@async_session_context
async def get_unique_welding_addition_for_welding(session: AsyncSession) -> Sequence[tuple[str, str]]:
    stmt = (
        select(
            Cassette.name,
            func.count(Cassette.name).label('count')
        )
        .filter(Cassette.state == CassetteState.CUTED)
        .filter(Cassette.type == CassetteType.WELDED)
        .filter(Cassette.in_working == False)
        .group_by(Cassette.name)
    )
    res = []
    data = (await session.execute(stmt)).all()
    for row in data:
        name, count = row
        res.append((f"{name} - {count}", name))
    return res


@async_session_context
async def get_last_cassette_number(session: AsyncSession, year_char: str, group: int, month: int):
    stmt = (
        select(Cassette.number)
        .where(
            Cassette.number.like(f"{year_char}{group}.{month}.%")
        )
    )

    numbers = (await session.execute(stmt)).scalars().all()
    return max([int(number.split('.')[-1]) + 1 for number in numbers] or [1])


@async_session_context
async def validate_number(session: AsyncSession, number: CassetteNumberModel):
    stmt = select(Cassette.number).where(Cassette.number == str(number))
    return (await session.scalars(stmt)).one_or_none() is None


@async_session_context
async def activate_welding_work(session: AsyncSession, task: WeldCassetteTaskModel, number: CassetteNumberModel):
    stmt_select_cassette = (
        select(Cassette)
        .order_by(Cassette.id)
        .filter(Cassette.type.in_([CassetteType.CASSETTE, CassetteType.REMOVABLE]))
        .filter(Cassette.state == CassetteState.CUTED)
        .filter(Cassette.in_working == False)
        .filter(hash_exp(Cassette.name, Cassette.technical_comment) == task.task_hash)
        .options(selectinload(Cassette.groups))
        .options(selectinload(Cassette.additions))
    )
    cassette: Cassette = (await session.scalars(stmt_select_cassette)).first()
    cassette.number = str(number)
    cassette.in_working = True
    cassette.weld_date = task.weld_date

    group = []

    for user in task.group:
        group.append(
            CassetteGroupMember(
                group_type=CassetteGroupMemberType.WELDER,
                tg_id=user.id,
                percent=1
            )
        )

    for user in task.help_group:
        group.append(
            CassetteGroupMember(
                group_type=CassetteGroupMemberType.WELDER_HELPER,
                tg_id=user.id,
                percent=1
            )
        )

    [cassette.groups.append(i) for i in group]

    await session.flush()

    raw_additions = task.raw_additions
    for raw_addition in raw_additions:
        stmt_select_addition = (
            select(Cassette)
            .order_by(desc(Cassette.priority))
            .order_by(Cassette.id)
            .filter(Cassette.type == CassetteType.WELDED)
            .filter(Cassette.state == CassetteState.CUTED)
            .filter(Cassette.in_working == False)
            .filter(Cassette.name == raw_addition)
            .options(selectinload(Cassette.groups))
        )
        addition = (await session.scalars(stmt_select_addition)).first()
        if addition is None:
            raise AdditionNotFoundException(f"Cassette with name '{raw_addition}' is not available or already in work.")
        addition.in_working = True
        addition.weld_date = task.weld_date
        [addition.groups.append(i) for i in group]
        await session.flush()
        cassette.additions.append(addition)

    return cassette


@async_session_context
async def deactivate_welding_work(session: AsyncSession, cassette_id: int) -> None:
    cassette = await session.get(
        Cassette,
        cassette_id,
        options=[
            selectinload(Cassette.groups),
            selectinload(Cassette.additions)
        ]
    )

    cassette.number = None
    cassette.in_working = False
    cassette.weld_date = None
    for group in cassette.groups:
        await session.delete(group)

    for addition in cassette.additions:
        await deactivate_welding_work(addition.id)


@async_session_context
async def finish_welding_work(session: AsyncSession, cassette_id: int) -> None:
    cassette = await session.get(
        Cassette,
        cassette_id,
        options=[
            selectinload(Cassette.additions)
        ]
    )

    cassette.in_working = False
    cassette.state = CassetteState.WELDED

    for addition in cassette.additions:
        addition.in_working = False
        addition.state = CassetteState.WELDED


@async_session_context
async def get_cassette_number_by_suffix(session: AsyncSession,cassette_state:str, suffix: int) -> Sequence[str]:
    stmt = (
        select(Cassette.number)
        .filter(Cassette.state == cassette_state)
        .filter(Cassette.number.like(f"%{suffix}"))
    )
    return (await session.scalars(stmt)).all()
