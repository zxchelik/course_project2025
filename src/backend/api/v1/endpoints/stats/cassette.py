from typing import Literal, Annotated

from fastapi import APIRouter, Query, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.api.v1.Models.stats.general import ProducedCount
from src.backend.database.models import Cassette
from src.backend.database.session_context import get_async_session

router = APIRouter(prefix="/cassette")

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
        select(Cassette.weld_date.label("date"), func.count(Cassette.id).label("count"))
        .filter(Cassette.weld_date != None)
        .group_by(Cassette.weld_date)
        .order_by(Cassette.weld_date.desc())
    )
    if limit:
        stmt = stmt.limit(limit)

    result = (await session.execute(stmt)).all()
    print(result)
    return [ProducedCount(produced_date=i[0], count=i[1]) for i in result[::-1]]
