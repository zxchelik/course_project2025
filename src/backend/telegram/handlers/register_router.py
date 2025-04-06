from aiogram import Dispatcher

from src.backend.telegram.handlers.admin.register_admins_router import admins_router
from src.backend.telegram.handlers.user.register_user_router import user_router


def register_router(dp: Dispatcher):
    admins_router(dp)
    user_router(dp)
