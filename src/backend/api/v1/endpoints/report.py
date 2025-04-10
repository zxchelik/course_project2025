from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime

from api.v1.dependencies.permissions import require_role
from database.get_exel.get_full_exel import get_full_exel_to_stream

router = APIRouter()


@router.get("/stats/report", tags=["Статистика"])
async def download_report(year: int, month: int, user=Depends(require_role("admin"))):
    stream = await get_full_exel_to_stream(year, month)

    filename = f"Report {year:02d}.{month:02d}.xlsx"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
