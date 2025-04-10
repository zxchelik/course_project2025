from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message

from database.db_cmd.user_cmd import check_status, is_admin


class CheckStatus(BaseFilter):
    def __init__(self, status: Union[str, list]):
        self.status = status

    async def __call__(self, message: Message) -> bool:  # [3]
        user_id = message.from_user.id
        return await check_status(tg_id=user_id, status=self.status)


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:  # [3]
        user_id = message.from_user.id
        return await is_admin(tg_id=user_id)
