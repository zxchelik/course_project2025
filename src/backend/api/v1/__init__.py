from fastapi import APIRouter
from .endpoints import routers

router_v1 = APIRouter(prefix="/v1")
for router in routers:
    router_v1.include_router(router)
