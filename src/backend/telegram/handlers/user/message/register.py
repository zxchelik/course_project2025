from aiogram import F
from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.filters.text import Text
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from src.backend import misc
from src.backend.telegram.utils.aiogram_calendar import dialog_callback_filter, DialogCalendar
from src.backend.database.db_cmd.user_cmd import add_user, get_admins, count_check_users

# from database.db_commands.user_cmd import add_user, get_admins, count_check_users
from src.backend.telegram.keyboards.inline import get_confirm_ikb
from src.backend.telegram.states.users import RegisterStates
from src.backend.text_templates import *

router = Router()
bot = misc.bot


async def send_admins_new_user() -> None:  # Отправляет админа уведомление о новом пользователе
    admins = await get_admins()
    text = f"""Зарегистрировались новые пользователи: {await count_check_users()}
Показать?
"""
    for admin in admins:
        id = admin.tg_id
        await bot.send_message(
            chat_id=id,
            text=text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Показать", callback_data="show_new_user")]],
            ),
        )


@router.message(Command("start"))  # Начало регистрации
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(hello_text)
    await state.set_state(RegisterStates.fio)
    await state.update_data(id=message.from_user.id)


@router.message(RegisterStates.fio, F.text)
async def get_fio(message: Message, state: FSMContext):
    await state.update_data(fio=message.text)
    await message.answer(text=select_birthday, reply_markup=await DialogCalendar().start_calendar(year=1990))
    await state.set_state(RegisterStates.birthday)


@router.callback_query(dialog_callback_filter, StateFilter(RegisterStates.birthday))
async def process_simple_calendar(callback_query: CallbackQuery, state: FSMContext):
    selected, date = await DialogCalendar().process_selection(callback_query)
    if selected:
        await state.update_data(date=date)
        user_data = await state.get_data()

        text = valid_reg.format(name=user_data.get("fio"), birthday=date.strftime("%d.%m.%Y"))
        await state.set_state(RegisterStates.confirm)
        await callback_query.message.edit_text(text, reply_markup=get_confirm_ikb(prefix="confirm"))


@router.callback_query(StateFilter(RegisterStates.confirm), Text(startswith="confirm_"))
async def get_birthday(callback: CallbackQuery, state: FSMContext):
    callback_data = callback.data.split("_")[1]
    if callback_data == "cancel":
        await callback.message.edit_text(re_reg)
        await state.set_state(RegisterStates.fio)
        return
    elif callback_data == "confirm":
        user_data = await state.get_data()
        await add_user(tg_id=user_data["id"], fio=user_data["fio"], birth_date=user_data["date"])
        await state.clear()
        text = wait_admins.format(name=user_data["fio"])
        await send_admins_new_user()
        await callback.message.edit_text(text=text)
