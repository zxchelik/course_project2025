import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.database.models.groups import Groups
from src.backend.database.models.user import User
from src.backend.database.session_context import async_session_context


@async_session_context
async def create_group(session: AsyncSession, users_id: list[int]) -> list:
    group = Groups()
    await session.flush()
    # group.users.append(USER(tg_id=1, fio="1", birthday=date.today()))

    for user_id in users_id:
        user = await session.get(User, user_id)
        group.users.append(user)
    session.add(group)
    percent = round(1 / len(users_id), 3)
    group_id = await session.scalars(select(Groups))
    return [group, percent]


if __name__ == "__main__":
    print(asyncio.run(create_group(users_id=[882490987, 6378810063])))
