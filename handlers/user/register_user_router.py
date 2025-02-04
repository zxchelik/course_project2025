from aiogram import Dispatcher

from .commands import add_container
from .commands import add_hourly_work
from .message import different
from .message import register
from .commands.cassette import cutting
from .commands.cassette import menu
from .commands.cassette import welding
from .commands.cassette import painting


def user_router(dp: Dispatcher):
    dp.include_router(register.router)
    dp.include_router(different.router)
    dp.include_router(add_container.router)
    dp.include_router(add_hourly_work.router)
    dp.include_router(menu.router)
    dp.include_router(cutting.router)
    dp.include_router(welding.router)
    dp.include_router(painting.router)
