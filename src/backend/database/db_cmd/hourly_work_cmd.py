from collections import defaultdict
from datetime import date

from sqlalchemy import select, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.database.models.hourly_work import HourlyWork
from src.backend.database.session_context import async_session_context


@async_session_context
async def add_hourly_work(
    session: AsyncSession, user_id: int, name: str, duration: float, date_: date, comment: str | None = None
) -> None:
    hw = HourlyWork(user_id=user_id, name=name, duration=duration, date_=date_, comment=comment)
    session.add(hw)


# @async_session_context
# async def get_all_hourly_work_by_month(session: AsyncSession, year, month) -> dict:
#     query = select(HourlyWork).where(extract("MONTH", HourlyWork.date_) == 9,
#                                      extract("YEAR", HourlyWork.date_) == 2023).options(selectinload(HourlyWork.user))
#     hw_list = (await session.scalars(query)).all()
#
#     data = {}
#     for hw in hw_list:
#         user_fio, info = hw.get_info_for_exel()
#         user_info: list = data.setdefault(user_fio, [])
#         user_info.append(info)
#
#     return data


@async_session_context
async def get_all_hourly_work_by_month(seesion: AsyncSession, year, month):
    query = (
        select(HourlyWork)
        .where(extract("MONTH", HourlyWork.date_) == month, extract("YEAR", HourlyWork.date_) == year)
        .options(selectinload(HourlyWork.user))
    )
    hw_list = (await seesion.scalars(query)).all()

    data = defaultdict(list)
    for hw in hw_list:
        user_fio, info = hw.get_info_for_exel()
        data[user_fio].append(info)
    for datum in data.values():
        datum.sort()
    return dict(data)


# @async_session_context
# async def get_user_hourly_work_by_month(session: AsyncSession, year, month, user_id: int) -> list[list]:
#     query = select(HourlyWork).where(extract("MONTH", HourlyWork.date_) == month,
#                                      extract("YEAR", HourlyWork.date_) == year,
#                                      HourlyWork.user_id == user_id)
#     print(query)
#     hw_list = (await session.scalars(query)).all()
#     data = []
#     for hw in hw_list:
#         _, info = hw.get_info_for_exel()
#         data.append(info)
#     return data
