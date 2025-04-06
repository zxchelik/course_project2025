from aiogram import Router, Bot
from aiogram.enums import ParseMode
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.backend.database.db_cmd.user_cmd import select_all_users
from src.backend.telegram.filters.db_filters import CheckStatus, IsAdmin
from src.backend.telegram.keyboards.inline import get_inline_kb
from src.backend.telegram.states.admin import Mailing

router = Router()


@router.callback_query(CheckStatus("active"), IsAdmin(), Text("mailing"))
async def start_mailing(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.update_data(msg=callback.message)
    mailing_text = data.get("mailing_text")
    text = "Введи текст рассылки"
    await state.set_state(Mailing.get_mailing)
    await callback.message.edit_text(text, parse_mode=ParseMode.MARKDOWN_V2)


@router.message(StateFilter(Mailing.get_mailing))
async def get_mailing_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    mailing_text = message.text
    kb = get_inline_kb([[("✅ Разослать", "yes"), ("✏️ Отредактировать", "no")]], "confirm")
    await state.set_state(Mailing.get_confirmed)
    await state.update_data(mailing_text=mailing_text)
    msg: Message = data.get("msg")
    await message.answer(mailing_text, reply_markup=kb)
    await message.delete()
    await msg.delete()


@router.callback_query(Text("confirm_no"))
async def confirm_no(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.update_data(msg=callback.message)
    mailing_text = data.get("mailing_text")
    text = f"```{mailing_text}```\n Введи исправленный текст рассылки"
    await state.set_state(Mailing.get_mailing)
    await callback.message.edit_text(text, parse_mode=ParseMode.MARKDOWN_V2)


@router.callback_query(Text("confirm_yes"))
async def confirm_yes(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    mailing_text = data.get("mailing_text")
    users = await select_all_users(admin=True)
    counter = [0, 0]
    for user in users:
        try:
            await bot.send_message(chat_id=user.tg_id, text=mailing_text)
            counter[0] += 1
        except Exception as e:
            counter[1] += 1
    await callback.message.delete()
    await callback.message.answer(f"Рассылка закончилась\n\n✅{counter[0]}\n❌{counter[1]}\n")
