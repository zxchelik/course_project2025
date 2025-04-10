from aiogram import Dispatcher

from telegram.handlers.admin.register_admins_router import admins_router
from telegram.handlers.user.register_user_router import user_router


def register_router(dp: Dispatcher):
    admins_router(dp)
    user_router(dp)
