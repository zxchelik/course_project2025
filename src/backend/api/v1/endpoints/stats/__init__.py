from fastapi import APIRouter, Depends
from . import container, cassette
from ...dependencies.permissions import require_role

router = APIRouter(prefix="/stats", tags=["Статистика"], dependencies=[Depends(require_role("Аналитик"))])


router.include_router(container.router)
router.include_router(cassette.router)
