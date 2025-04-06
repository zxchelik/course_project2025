import os
from datetime import date

from aiogram import Router, Bot
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile

from src.backend.telegram.utils.aiogram_calendar import calendar_callback_filter, SimpleCalendar
from src.backend.telegram.filters.db_filters import CheckStatus, IsAdmin
from src.backend.telegram.keyboards.inline import get_confirm_ikb
from src.backend.telegram.states.admin import GetStats
from src.backend.text_templates import confirm_date_text
from src.backend.telegram.utils.containers_statistic import get_containers_statistic

router = Router()


@router.callback_query(CheckStatus("active"), IsAdmin(), Text("get_stats"))
async def get_first_date(callback: CallbackQuery, state: FSMContext):
    await state.update_data(type=callback.data)
    now_date = date.today()
    await callback.message.edit_text(
        text="Выберите с какого числа вывести данные",
        reply_markup=await SimpleCalendar().start_calendar(year=now_date.year, month=now_date.month),
    )
    await state.set_state(GetStats.get_first_date)


@router.callback_query(Text(startswith="confirm_"), StateFilter(GetStats.get_first_date))
async def confirm_first_date(callback: CallbackQuery, state: FSMContext):
    update_code = callback.data.split("_")[1]
    if update_code == "cancel":
        data = (await state.get_data()).setdefault("date")
        data.pop()
        await state.update_data(data=data)
        await get_first_date(callback, state)
    elif update_code == "confirm":
        await state.set_state(GetStats.get_last_date)
        await get_last_date(callback, state)


async def get_last_date(callback: CallbackQuery, state: FSMContext):
    now_date = date.today()
    await callback.message.edit_text(
        text="Выберите по какое число вывести данные",
        reply_markup=await SimpleCalendar().start_calendar(year=now_date.year, month=now_date.month),
    )
    await state.set_state(GetStats.get_last_date)


@router.callback_query(Text(startswith="confirm_"), StateFilter(GetStats.get_last_date))
async def confirm_last_date(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    update_code = callback.data.split("_")[1]
    if update_code == "cancel":
        data = (await state.get_data()).setdefault("date")
        data.pop()
        await state.update_data(data=data)
        await get_last_date(callback, state)
    elif update_code == "confirm":
        await start_get_containers(callback, state, bot)


@router.callback_query(calendar_callback_filter, StateFilter(GetStats))
async def process_simple_calendar(callback_query: CallbackQuery, state: FSMContext):
    selected, date_ = await SimpleCalendar().process_selection(callback_query)
    if selected:
        stored_date = (await state.get_data()).setdefault("date", [])
        stored_date.append(date_)
        await state.update_data(date=stored_date)
        await callback_query.message.answer(
            confirm_date_text.format(date=date_.strftime("%d.%m.%Y")), reply_markup=get_confirm_ikb(prefix="confirm")
        )


async def start_get_containers(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.message.edit_text("Генерирую файл...")
    data = await state.get_data()
    first_date, last_date = data.get("date")

    filename = await get_containers_statistic(first_date, last_date)

    await callback.message.delete()
    await bot.send_document(callback.message.chat.id, FSInputFile(filename))
    os.remove(filename)
