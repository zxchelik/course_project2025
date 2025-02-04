from typing import Sequence

from sqlalchemy import Insert, select, not_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.names import Names
from database.session_context import async_session_context


@async_session_context
async def add_name(session: AsyncSession, name: str, parent_id: int, **kwargs) -> None:
    query = Insert(Names).values(name=name, parent_id=parent_id, **kwargs)
    await session.execute(query)


@async_session_context
async def select_names(session: AsyncSession, parent_id: int) -> Sequence[Names]:
    query = select(Names).where(Names.parent_id == parent_id).order_by(Names.id)
    names = await session.execute(query)
    return names.scalars().all()


@async_session_context
async def select_name(session: AsyncSession, id: int) -> Names:
    query = select(Names).where(Names.id == id)
    names = await session.execute(query)
    return names.scalars().one()


@async_session_context
async def get_parent_id(session: AsyncSession, id: int) -> int:
    query = select(Names.parent_id).where(Names.id == id)
    names = await session.execute(query)
    return names.scalars().one()


@async_session_context
async def get_parent(session: AsyncSession, id: int) -> Names:
    query = select(Names).where(Names.id == id)
    names = await session.execute(query)
    return names.scalars().one()


@async_session_context
async def select_product(session: AsyncSession) -> Sequence[Names]:
    subquery = select(Names.parent_id).where(Names.parent_id != None).distinct()
    query = select(Names).where(not_(Names.id.in_(subquery))).order_by(Names.parent_id)
    return (await session.execute(query)).scalars().all()


@async_session_context
async def update(session: AsyncSession, id: int, points: float = None, price: float = None):
    p = await session.get(Names, id)
    p.points = points
    p.price = price
    await session.commit()


@async_session_context
async def get_product_dict(session: AsyncSession) -> dict:
    subquery = select(Names.parent_id).where(Names.parent_id != None).distinct()
    query = select(Names).where(not_(Names.id.in_(subquery))).order_by(Names.parent_id)

    products = (await session.execute(query)).scalars().all()

    res = dict()

    for product in products:
        res[product.id] = product

    return res
