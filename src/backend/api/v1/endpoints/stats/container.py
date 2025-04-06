from typing import Literal, Annotated

from fastapi import APIRouter, Query, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.api.v1.Models.stats.general import ProducedCount
from src.backend.database.models import Container
from src.backend.database.session_context import get_async_session

router = APIRouter(prefix="/container")

PeriodType = Annotated[Literal["week", "month", "all"], Query(description="Один из вариантов: week, month, all")]


@router.get("/produced_count", response_model=list[ProducedCount])
async def get_produced_count(
    period: PeriodType,
    session: AsyncSession = Depends(get_async_session),
):
    limit = None
    if period == "week":
        limit = 7
    elif period == "month":
        limit = 30
    stmt = (
        select(Container.date_cont.label("date"), func.count(Container.id).label("count"))
        .group_by(Container.date_cont)
        .order_by(Container.date_cont.desc())
    )
    if limit:
        stmt = stmt.limit(limit)

    result = (await session.execute(stmt)).all()
    return [ProducedCount(produced_date=i[0], count=i[1]) for i in result[::-1]]


@router.get("/top_colors")
async def get_top_colors(count: int = 10, session: AsyncSession = Depends(get_async_session)):
    color_counts = (
        await session.execute(
            select(Container.color, func.count(Container.id).label("count"))
            .group_by(Container.color)
            .order_by(func.count(Container.id).desc())
        )
    ).all()

    # Берём 9 самых популярных цветов
    top9 = color_counts[:9]

    # Остальные цвета объединяем в отдельную группу
    others = color_counts[9:]
    others_total = sum(item.count for item in others) if others else 0

    # Формируем результат в виде списка словарей
    result = [{"color": color, "count": count} for color, count in top9]

    # Если есть «прочие» цвета, добавляем их в результат
    if others_total:
        result.append({"color": "others", "count": others_total})

    return result
