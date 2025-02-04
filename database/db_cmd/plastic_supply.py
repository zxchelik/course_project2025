from typing import Sequence

from sqlalchemy import func, select, not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from ..models.container import Container
from ..models.plastic_supply import PlasticSupply
from ..session_context import async_session_context


@async_session_context
async def get_plastic_residue(session: AsyncSession):
    """Возвращает массив кортежей (color, total_weight)"""
    used_alias = aliased(
        select(
            Container.color.label('color'),
            func.coalesce(func.sum(Container.weight), 0).label('total_weight'),
        )
        .where(not_(Container.number.contains("-")))
        .group_by(Container.color).subquery()
    )

    # Подзапрос для суммирования привезенного пластика по цветам в таблице поставок
    supplied_alias = aliased(
        select(
            PlasticSupply.color_number.label('color'),
            func.sum(PlasticSupply.weight).label('total_weight'),
        ).group_by(PlasticSupply.color_number).subquery()
    )

    # Основной запрос для вычисления остатка пластика
    query = (
        select(
            func.coalesce(supplied_alias.c.color, used_alias.c.color).label('color'),
            (
                    func.coalesce(supplied_alias.c.total_weight, 0) - func.coalesce(used_alias.c.total_weight, 0)
            ).label('total_weight')
        )
        .order_by(supplied_alias.c.color)
        .outerjoin(used_alias, supplied_alias.c.color == used_alias.c.color, full=True)
    )

    return (await session.execute(query)).all()


@async_session_context
async def get_all_colors(session: AsyncSession) -> Sequence[int]:
    stmt = select(PlasticSupply.color_number).order_by(PlasticSupply.color_number).distinct()
    return (await session.scalars(stmt)).all()
