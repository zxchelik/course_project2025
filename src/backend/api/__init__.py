from fastapi import APIRouter
from .v1 import router_v1

main_api_router = APIRouter(prefix="/api")
main_api_router.include_router(router_v1)
