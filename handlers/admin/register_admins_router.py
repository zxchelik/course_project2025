from aiogram import Dispatcher

from .callback import different
from .callback import register_callback
from .commands import add_cassette_task
from .commands import add_name
from .commands import get_availability
from .commands import get_plastic_residue
from .commands import get_report
from .commands import get_stats
from .commands import mailing


def admins_router(dp: Dispatcher):
    dp.include_router(register_callback.router)
    dp.include_router(add_name.router)
    dp.include_router(get_report.router)
    dp.include_router(different.router)
    dp.include_router(get_stats.router)
    dp.include_router(mailing.router)
    dp.include_router(get_availability.router)
    dp.include_router(get_plastic_residue.router)
    dp.include_router(add_cassette_task.router)
