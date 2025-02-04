from typing import Union

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from database.db_cmd.user_cmd import get_groups

confirm_kb = ReplyKeyboardMarkup(resize_keyboard=True,
                                 keyboard=[[KeyboardButton(text="Всё верно ✅")],
                                           [KeyboardButton(text="Есть ошибка ❌")]], one_time_keyboard=True)


async def get_group_list() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for group in await get_groups():
        if group != None:
            builder.add(KeyboardButton(text=group))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_reply_keyboard(buttons: Union[str, list]) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    if type(buttons) == list:
        for button in buttons:
            if type(buttons) == list:
                builder.row(*[KeyboardButton(text=text) for text in button])
            else:
                builder.add(KeyboardButton(text=button))
    else:
        builder.add(KeyboardButton(text=buttons))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
