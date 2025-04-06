from datetime import date
from typing import Sequence

from sqlalchemy import Insert, select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.database.models.user import User
from src.backend.database.modelsDTO.user import UserIdFioModel
from src.backend.database.session_context import async_session_context


@async_session_context
async def add_user(session: AsyncSession, tg_id: int, fio: str, birth_date: date, **kwargs) -> None:
    query = Insert(User).values(tg_id=tg_id, fio=fio, birthday=birth_date, **kwargs)
    await session.execute(query)


@async_session_context
async def select_user(session: AsyncSession, tg_id: int) -> User | None:
    query = select(User).where(User.tg_id == tg_id)
    user = await session.execute(query)

    return user.scalars().one()


@async_session_context
async def select_all_users(session: AsyncSession, admin=False) -> Sequence[User]:
    if admin:
        query = select(User).where(User.status == "active")
    else:
        query = select(User).where(and_(User.is_admin == False, User.status == "active"))
    user = await session.execute(query)
    return user.scalars().all()


@async_session_context
async def activate_user(session: AsyncSession, tg_id: int) -> None:
    query = update(User).where(User.tg_id == tg_id).values(status="active")
    await session.execute(query)


@async_session_context
async def deactivate_user(session: AsyncSession, tg_id: int) -> None:
    query = update(User).where(User.tg_id == tg_id).values(status="deactive")
    await session.execute(query)


@async_session_context
async def give_admin(session: AsyncSession, tg_id: int):
    query = update(User).where(User.tg_id == tg_id).values(is_admin=True)
    await session.execute(query)


@async_session_context
async def check_status(session: AsyncSession, tg_id: int, status: str | list) -> bool:
    query = select(User.status).where(User.tg_id == tg_id)
    user_status = await session.execute(query)
    user_status = user_status.scalars().one_or_none()
    if not user_status:
        return False
    match isinstance(status, list):
        case True:
            return user_status in status
        case False:
            return user_status == status


@async_session_context
async def is_admin(session: AsyncSession, tg_id: int) -> bool:
    query = select(User.is_admin).where(User.tg_id == tg_id)
    admin = (await session.scalars(query)).one_or_none()
    if admin:
        return admin
    else:
        return False


@async_session_context
async def update_group(session: AsyncSession, tg_id: int, new_group: str):
    query = update(User).where(User.tg_id == tg_id).values(group=new_group)
    await session.execute(query)


@async_session_context
async def get_admins(session: AsyncSession) -> Sequence[User]:
    query = select(User).where(User.is_admin == True)
    users = await session.execute(query)
    return users.scalars().all()


@async_session_context
async def get_new_user(session: AsyncSession) -> User | None:
    query = select(User).where(User.status == "check")
    user = await session.execute(query)
    return user.scalars().one_or_none()


@async_session_context
async def count_check_users(session: AsyncSession) -> int:
    query = select(User).where(User.status == "check")
    users = await session.execute(query)
    return len(users.scalars().all())


@async_session_context
async def del_user(session: AsyncSession, tg_id: int) -> None:
    query = delete(User).where(User.tg_id == tg_id)
    await session.execute(query)


@async_session_context
async def get_groups(session: AsyncSession) -> Sequence[str]:
    query = select(User.group)
    groups = await session.execute(query)
    return groups.scalars().unique().all()


@async_session_context
async def get_users(session: AsyncSession, users_id: list[int]) -> Sequence[str]:
    res = []
    for user_id in users_id:
        query = select(User.fio).where(User.tg_id == user_id)
        users_fio = await session.execute(query)
        res.append(users_fio.scalars().one())
    return res


@async_session_context
async def get_user(session: AsyncSession, user_id: int) -> User:
    query = select(User).where(User.tg_id == user_id)
    return (await session.execute(query)).scalars().one()


@async_session_context
async def get_all_users_for_group_select(session: AsyncSession) -> list[UserIdFioModel]:
    stmt = select(User).filter(User.is_admin == False).filter(User.status == "active")
    res = (await session.scalars(stmt)).all()
    return [UserIdFioModel(id=i.tg_id, fio=i.fio) for i in res]
