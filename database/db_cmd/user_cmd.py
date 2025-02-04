from datetime import date
from typing import Sequence

from sqlalchemy import Insert, select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import USER
from database.modelsDTO.user import UserIdFioModel
from database.session_context import async_session_context


@async_session_context
async def add_user(session: AsyncSession, tg_id: int, fio: str, birth_date: date,
                   **kwargs) -> None:
    query = Insert(USER).values(tg_id=tg_id, fio=fio, birthday=birth_date,
                                **kwargs)
    await session.execute(query)


@async_session_context
async def select_user(session: AsyncSession, tg_id: int) -> USER | None:
    query = select(USER).where(USER.tg_id == tg_id)
    user = await session.execute(query)

    return user.scalars().one()


@async_session_context
async def select_all_users(session: AsyncSession, admin=False) -> Sequence[USER]:
    if admin:
        query = select(USER).where(USER.status == "active")
    else:
        query = (
            select(USER).where(
                and_(USER.is_admin == False,
                     USER.status == "active")
            )
        )
    user = await session.execute(query)
    return user.scalars().all()


@async_session_context
async def activate_user(session: AsyncSession, tg_id: int) -> None:
    query = update(USER).where(USER.tg_id == tg_id).values(status="active")
    await session.execute(query)


@async_session_context
async def deactivate_user(session: AsyncSession, tg_id: int) -> None:
    query = update(USER).where(USER.tg_id == tg_id).values(status="deactive")
    await session.execute(query)


@async_session_context
async def give_admin(session: AsyncSession, tg_id: int):
    query = update(USER).where(USER.tg_id == tg_id).values(is_admin=True)
    await session.execute(query)


@async_session_context
async def check_status(session: AsyncSession, tg_id: int, status: str | list) -> bool:
    query = select(USER.status).where(USER.tg_id == tg_id)
    user_status = await session.execute(query)
    user_status = user_status.scalars().one()
    match isinstance(status, list):
        case True:
            return user_status in status
        case False:
            return user_status == status


@async_session_context
async def is_admin(session: AsyncSession, tg_id: int) -> bool:
    query = select(USER.is_admin).where(USER.tg_id == tg_id)
    admin = await session.execute(query)
    return admin.scalars().one()


@async_session_context
async def update_group(session: AsyncSession, tg_id: int, new_group: str):
    query = update(USER).where(USER.tg_id == tg_id).values(group=new_group)
    await session.execute(query)


@async_session_context
async def get_admins(session: AsyncSession) -> Sequence[USER]:
    query = select(USER).where(USER.is_admin == True)
    users = await session.execute(query)
    return users.scalars().all()


@async_session_context
async def get_new_user(session: AsyncSession) -> USER | None:
    query = select(USER).where(USER.status == "check")
    user = await session.execute(query)
    return user.scalars().one_or_none()


@async_session_context
async def count_check_users(session: AsyncSession) -> int:
    query = select(USER).where(USER.status == "check")
    users = await session.execute(query)
    return len(users.scalars().all())


@async_session_context
async def del_user(session: AsyncSession, tg_id: int) -> None:
    query = delete(USER).where(USER.tg_id == tg_id)
    await session.execute(query)


@async_session_context
async def get_groups(session: AsyncSession) -> Sequence[str]:
    query = select(USER.group)
    groups = await session.execute(query)
    return groups.scalars().unique().all()


@async_session_context
async def get_users(session: AsyncSession, users_id: list[int]) -> Sequence[str]:
    res = []
    for user_id in users_id:
        query = select(USER.fio).where(USER.tg_id == user_id)
        users_fio = await session.execute(query)
        res.append(users_fio.scalars().one())
    return res


@async_session_context
async def get_user(session: AsyncSession, user_id: int) -> USER:
    query = select(USER).where(USER.tg_id == user_id)
    return (await session.execute(query)).scalars().one()


@async_session_context
async def get_all_users_for_group_select(session: AsyncSession) -> list[UserIdFioModel]:
    stmt = (
        select(USER)
        .filter(USER.is_admin == False)
        .filter(USER.status == "active")
    )
    res = (await session.scalars(stmt)).all()
    return [UserIdFioModel(id=i.tg_id, fio=i.fio) for i in res]
