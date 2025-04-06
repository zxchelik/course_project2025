import asyncio
import calendar
import datetime
import re
from collections import defaultdict
from typing import Sequence, Callable, Awaitable

from sqlalchemy import select, func, desc, text, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.database.db_cmd.Exceptions import AdditionNotFoundException
from src.backend.database.models import Cassette, CassetteGroupMember
from src.backend.database.models.blank_cassettes import CassetteType
from src.backend.database.models.cassette import CassetteState
from src.backend.database.models.cassette_group_member import CassetteGroupMemberType
from src.backend.database.modelsDTO.cassette import (
    CassetteNQHModel,
    CassetteNumberModel,
    RawCassetteModel,
    WeldCassetteTaskModel,
)
from src.backend.database.modelsDTO.paint_task import PaintingTask
from src.backend.database.session_context import async_session_context

help_user_percent = 0.5


@async_session_context
async def add_cassette(
    session: AsyncSession,
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
        [
            Cassette(
                name=name,
                priority=priority,
                type=type,
                cut_date=cut_date,
                cutter_id=cutter_id,
                technical_comment=technical_comment,
                comment=comment,
            )
            for _ in range(quantity)
        ]
    )
    await session.commit()


def hash_exp(name, tcomment):
    return func.md5(func.concat(name, "|", tcomment))


@async_session_context
async def get_tasks_for_welding(session: AsyncSession) -> list[CassetteNQHModel]:
    stmt = (
        select(
            Cassette.name,
            func.count(Cassette.id).label("quantity"),
            hash_exp(Cassette.name, Cassette.technical_comment).label("hash"),
        )
        .order_by(desc(Cassette.priority))
        .filter(Cassette.state == CassetteState.CUT)
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
        .filter(Cassette.state == CassetteState.CUT)
        .filter(Cassette.type != CassetteType.WELDED)
        .filter(Cassette.in_working == False)
        .filter(hash_exp(Cassette.name, Cassette.technical_comment) == task_hash)
    )

    res = (await session.execute(stmt)).scalars().first()
    return RawCassetteModel.from_orm(res)


@async_session_context
async def get_max_quantity_for_welding_by_hash(session: AsyncSession, task_hash: str):
    q = select(hash_exp(Cassette.name, Cassette.technical_comment).label("hash")).subquery()
    stmt = select(func.count(q.c.hash)).filter(q.c.hash == task_hash).group_by(q.c.hash)
    return (await session.execute(stmt)).scalars().first()


@async_session_context
async def get_unique_welding_addition_for_welding(session: AsyncSession) -> Sequence[tuple[str, str]]:
    stmt = (
        select(Cassette.name, func.count(Cassette.name).label("count"))
        .filter(Cassette.state == CassetteState.CUT)
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
    stmt = select(Cassette.number).where(Cassette.number.like(f"{year_char}{group}.{month}.%"))

    numbers = (await session.execute(stmt)).scalars().all()
    return max([int(number.split(".")[-1]) + 1 for number in numbers] or [1])


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
        .filter(Cassette.state == CassetteState.CUT)
        .filter(Cassette.in_working == False)
        .filter(hash_exp(Cassette.name, Cassette.technical_comment) == task.task_hash)
        .options(selectinload(Cassette.groups))
        .options(selectinload(Cassette.additions))
    )
    cassette: Cassette = (await session.scalars(stmt_select_cassette)).first()
    cassette.number = str(number)
    cassette.in_working = True
    cassette.weld_date = task.weld_date

    super_group = task.group + (task.help_group or [])

    for user in task.group:
        cassette.groups.append(CassetteGroupMember(group_type=CassetteGroupMemberType.WELDER, tg_id=user.id))
    for user in task.help_group:
        cassette.groups.append(CassetteGroupMember(group_type=CassetteGroupMemberType.WELDER_HELPER, tg_id=user.id))

    await session.flush()

    raw_additions = task.raw_additions
    for raw_addition in raw_additions:
        stmt_select_addition = (
            select(Cassette)
            .order_by(desc(Cassette.priority))
            .order_by(Cassette.id)
            .filter(Cassette.type == CassetteType.WELDED)
            .filter(Cassette.state == CassetteState.CUT)
            .filter(Cassette.in_working == False)
            .filter(Cassette.name == raw_addition)
            .options(selectinload(Cassette.groups))
        )
        addition = (await session.scalars(stmt_select_addition)).first()
        if addition is None:
            raise AdditionNotFoundException(f"Cassette with name '{raw_addition}' is not available or already in work.")
        addition.in_working = True
        addition.weld_date = task.weld_date
        for user in task.group:
            addition.groups.append(CassetteGroupMember(group_type=CassetteGroupMemberType.WELDER, tg_id=user.id))
        for user in task.help_group:
            addition.groups.append(CassetteGroupMember(group_type=CassetteGroupMemberType.WELDER_HELPER, tg_id=user.id))

        await session.flush()
        cassette.additions.append(addition)

    return cassette


@async_session_context
async def deactivate_welding_work(session: AsyncSession, cassette_id: int) -> None:
    cassette = await session.get(
        Cassette, cassette_id, options=[selectinload(Cassette.groups), selectinload(Cassette.additions)]
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
    cassette = await session.get(Cassette, cassette_id, options=[selectinload(Cassette.additions)])

    cassette.in_working = False
    cassette.state = CassetteState.WELD

    for addition in cassette.additions:
        addition.in_working = False
        addition.state = CassetteState.WELD


@async_session_context
async def get_cassette_number_by_suffix_painting(session: AsyncSession, suffix: int) -> Sequence[str]:
    stmt = (
        select(Cassette.number)
        .filter(
            or_(
                Cassette.state == CassetteState.WELD,
                and_(Cassette.state == CassetteState.PAINT, Cassette.in_working == True),
            )
        )
        .filter(Cassette.number.like(f"%{suffix:02d}"))
    )
    return (await session.scalars(stmt)).all()


@async_session_context
async def get_cassette_number_by_suffix_assembling(
    session: AsyncSession, suffix: int, cassette_type: str = CassetteType.CASSETTE
) -> Sequence[str]:
    if cassette_type not in [CassetteType.REMOVABLE, CassetteType.CASSETTE]:
        raise ValueError("Incorrect cassette_type")
    stmt = (
        select(Cassette.number)
        .filter(Cassette.type == cassette_type)
        .filter(or_(Cassette.state == CassetteState.PAINT, Cassette.state == CassetteState.ASSEMBLE))
        .filter(Cassette.number.like(f"%{suffix:02d}"))
        .filter(Cassette.cassette_id == None)
    )
    return (await session.scalars(stmt)).all()


@async_session_context
async def get_cassette_info_for_excel(session: AsyncSession, month: int, year: int, cassette_state: int) -> dict:
    """
    Получает записи за указанный месяц и год и группирует их в словарь по полю u.fio.

    :param cassette_state: Запрашиваемый этап (2-4)
    :param session: Database сессия
    :param month: Номер месяца (1-12)
    :param year: Год (например, 2025)
    :return: dict[str, list]
    """
    # Определяем дату начала и окончания месяца
    start_date = datetime.date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    # Дата окончания - первый день следующего месяца
    end_date = datetime.date(year, month, last_day) + datetime.timedelta(days=1)

    date_type = [
        "weld_date",
        "paint_date",
        "assemble_date",
    ][cassette_state - 2]
    group_type = ["'Св', 'СвП'", "'М(1)', 'М(2)', 'М(3)'", "'Сб', 'СбП'"][cassette_state - 2]

    paint_where = """CASE cgm.group_type
WHEN 'М(1)' THEN 0.2
WHEN 'М(2)' THEN 0.4
WHEN 'М(3)' THEN 0.4
END AS impact,"""

    sql_query = text(
        f"""
    SELECT 
        CASE 
          WHEN ROW_NUMBER() OVER (
                PARTITION BY cgm.tg_id, c.weld_date 
                ORDER BY 
                        cgm.tg_id,
                        cgm.group_type,
                        c.{date_type},
                        COALESCE(c.cassette_id, c.id),
                        CASE WHEN c.cassette_id IS NULL THEN 0 ELSE 1 END, c.id
              ) = 1 
          THEN c.{date_type}
          ELSE NULL 
        END AS date,
        c.number,
        c.name,
        1 AS constant_value,
        {paint_where if cassette_state == 3 else "NULL AS impact,"}
        cgm.group_type,
        u.fio
    FROM cassette AS c
    LEFT JOIN cassette_group_member cgm ON c.id = cgm.cassette_id
    LEFT JOIN user_data u ON cgm.tg_id = u.tg_id
    WHERE (CASE c.state
     WHEN 'Нарезанная'  THEN 1
     WHEN 'Сваренная'    THEN 2
     WHEN 'Покрашенная'  THEN 3
     WHEN 'Собранная'    THEN 4
     WHEN 'Отгруженная'  THEN 5
   END) >= :min_state
      AND c.{date_type} >= :start_date
      AND c.{date_type} < :end_date
      AND cgm.group_type IN ({group_type})
    ORDER BY 
      cgm.tg_id,
      cgm.group_type, 
      c.{date_type},
--       c.number,
      COALESCE(c.cassette_id, c.id),         
      CASE WHEN c.cassette_id IS NULL THEN 0 ELSE 1 END,  
      c.id;
    """
    )

    # Выполняем запрос с параметрами
    result = (
        await session.execute(sql_query, {"start_date": start_date, "end_date": end_date, "min_state": cassette_state})
    ).fetchall()

    # Группируем результаты в словарь, где ключ – fio, а значение – список записей
    records_by_fio = defaultdict(list)
    for row in result:
        fio = row.fio
        data = [
            row.date.strftime("%d.%m.%y") if row.date else None,
            row.number,
            row.name,
            row.constant_value,
            row.impact or None,
            row.group_type,
        ]
        records_by_fio[fio].append(data)

    return dict(records_by_fio)


@async_session_context
async def get_cassette_cutting_for_excel(session: AsyncSession, month: int, year: int) -> dict:
    """
    Получает записи за указанный месяц и год и группирует их в словарь по полю u.fio.

    :param session: Database сессия
    :param month: Номер месяца (1-12)
    :param year: Год (например, 2025)
    :return: dict[str, list]
    """
    # Определяем дату начала и окончания месяца
    start_date = datetime.date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    # Дата окончания - первый день следующего месяца
    end_date = datetime.date(year, month, last_day) + datetime.timedelta(days=1)

    sql_query = text(
        f"""
    SELECT
    CASE
        WHEN ROW_NUMBER() OVER (
            PARTITION BY u.tg_id, c.cut_date
            ORDER BY
                c.cut_date,
                c.number,
                COALESCE(c.cassette_id, c.id),
                CASE WHEN c.cassette_id IS NULL THEN 0 ELSE 1 END,
                c.id
        ) = 1
        THEN c.cut_date
        ELSE NULL
    END AS cut_date,
    c.number,
    c.name,
    1 AS constant_value,
    'Нарезка' AS group_type,
    u.fio
FROM cassette AS c
JOIN user_data AS u ON c.cutter_id = u.tg_id
WHERE c.cut_date >= :start_date
  AND c.cut_date < :end_date
ORDER BY
    u.tg_id,
    c.cut_date,
    c.number,
    COALESCE(c.cassette_id, c.id),
    CASE WHEN c.cassette_id IS NULL THEN 0 ELSE 1 END,
    c.id;
    """
    )

    # Выполняем запрос с параметрами
    result = (await session.execute(sql_query, {"start_date": start_date, "end_date": end_date})).fetchall()

    # Группируем результаты в словарь, где ключ – fio, а значение – список записей
    records_by_fio = defaultdict(list)
    for row in result:
        fio = row.fio
        data = [
            row.cut_date.strftime("%d.%m.%y") if row.cut_date else None,
            row.number,
            row.name,
            row.constant_value,
            None,
            row.group_type,
        ]
        records_by_fio[fio].append(data)

    return dict(records_by_fio)


@async_session_context
async def get_cassette_painting_for_excel(session: AsyncSession, month: int, year: int) -> dict:
    """
    Получает записи за указанный месяц и год и группирует их в словарь по полю u.fio.

    :param session: Database сессия
    :param month: Номер месяца (1-12)
    :param year: Год (например, 2025)
    :return: dict[str, list]
    """
    # Определяем дату начала и окончания месяца
    start_date = datetime.date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    # Дата окончания - первый день следующего месяца
    end_date = datetime.date(year, month, last_day) + datetime.timedelta(days=1)

    sql_query = text(
        f"""WITH aggregated AS (
  SELECT 
    c.paint_date,
    c.number,
    c.name,
    1 AS constant_value,
    SUM(
      CASE cgm.group_type
        WHEN 'М(1)' THEN 0.2
        WHEN 'М(2)' THEN 0.4
        WHEN 'М(3)' THEN 0.4
      END
    ) AS impact,
    STRING_AGG(DISTINCT cgm.group_type, ',') AS group_types,
    u.fio,
    u.tg_id
  FROM cassette c
  LEFT JOIN cassette_group_member cgm ON c.id = cgm.cassette_id
  LEFT JOIN user_data u ON cgm.tg_id = u.tg_id
  WHERE (CASE c.state
           WHEN 'Нарезанная'  THEN 1
           WHEN 'Сваренная'    THEN 2
           WHEN 'Покрашенная'  THEN 3
           WHEN 'Собранная'    THEN 4
           WHEN 'Отгруженная'  THEN 5
         END) >= 3
    AND c.paint_date >= :start_date
    AND c.paint_date < :end_date
    AND cgm.group_type IN ('М(1)', 'М(2)', 'М(3)')
  GROUP BY c.id, u.tg_id, c.paint_date, c.number, c.name, u.fio
  ORDER BY u.tg_id, c.paint_date
)
SELECT 
  CASE 
    WHEN paint_date = LAG(paint_date) OVER (PARTITION BY tg_id ORDER BY paint_date)
         AND fio = LAG(fio) OVER (PARTITION BY tg_id ORDER BY paint_date)
      THEN NULL 
    ELSE paint_date 
  END AS date,
  number,
  name,
  constant_value,
  impact,
  group_types,
  fio
FROM aggregated;
"""
    )

    # Выполняем запрос с параметрами
    result = (await session.execute(sql_query, {"start_date": start_date, "end_date": end_date})).fetchall()

    # Группируем результаты в словарь, где ключ – fio, а значение – список записей
    records_by_fio = defaultdict(list)
    for row in result:
        fio = row.fio
        data = [
            row.date.strftime("%d.%m.%y") if row.date else None,
            row.number,
            row.name,
            row.constant_value,
            None,
            row.group_types,
        ]
        records_by_fio[fio].append(data)

    return dict(records_by_fio)


def get_cassette_info_func_generator(cassette_state: int) -> Callable[..., Awaitable[dict]]:
    async def wrapped_get_info_func(*, month: int, year: int) -> dict:
        return await get_cassette_info_for_excel(month=month, year=year, cassette_state=cassette_state)

    return wrapped_get_info_func


@async_session_context
async def get_painting_states_by_id(session: AsyncSession, cassette_id: int) -> set[int]:
    stmt = text(
        """
select
	cgm.group_type as group_type
from
	cassette_group_member cgm
where cgm.cassette_id = :id;
    """
    )
    res = (await session.execute(stmt, {"id": cassette_id})).scalars().all()
    pattern = re.compile(r"М\((\d+)\)")
    numbers = set()
    for group_type in res:
        match = pattern.search(group_type)
        if match:
            numbers.add(int(match.group(1)))

    return numbers


@async_session_context
async def paint_cassette(session: AsyncSession, task: PaintingTask, cassette_id: int | None = None):
    if cassette_id is None:
        cassette_id = task.cassette.id
    cassette = await session.get(
        Cassette, cassette_id, options=[selectinload(Cassette.groups), selectinload(Cassette.additions)]
    )
    [cassette.groups.append(CassetteGroupMember(tg_id=task.user_id, group_type=i)) for i in task.get_types_result()]
    cassette.state = CassetteState.PAINT
    cassette.in_working = not task.is_finished
    if cassette.paint_date:
        cassette.paint_date = max(Cassette.paint_date, task.painting_date)
    else:
        cassette.paint_date = task.painting_date
    await asyncio.gather(*[paint_cassette(task=task, cassette_id=add.id) for add in cassette.additions])
    await session.commit()
