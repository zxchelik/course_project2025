from enum import IntEnum
from typing import Union, Optional, List

from aiogram.types import (
    UNSET,
    MessageEntity,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ForceReply,
)

from src.backend.envfile import conf
from src.backend.misc import bot


class ReportType(IntEnum):
    CONTAINER = 2
    CUTTING = 3
    WELDING = 4
    PAINTING = 5
    ASSEMBLING = 7
    SHIPPING = 8
    HOURLY_WORK = 24


async def forward_report(
    report_type: ReportType,
    text: str,
    parse_mode: Optional[str] = UNSET,
    entities: Optional[List[MessageEntity]] = None,
    disable_web_page_preview: Optional[bool] = None,
    disable_notification: Optional[bool] = None,
    protect_content: Optional[bool] = None,
    reply_to_message_id: Optional[int] = None,
    allow_sending_without_reply: Optional[bool] = None,
    reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]] = None,
):
    chat_id = conf.bot.spam_id
    if conf.test:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            message_thread_id=report_type.value,
            parse_mode=parse_mode,
            entities=entities,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
