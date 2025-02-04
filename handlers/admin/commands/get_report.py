import datetime
import os

from aiogram import Router, F
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile
from loguru import logger

from database.get_exel.get_full_exel import get_full_exel
from filters.db_filters import CheckStatus
from keyboards.inline import get_select_month, SelectMonth
from states.admin import GetReport

router = Router()


@router.callback_query(CheckStatus('active'), Text('get_report'))
async def start_get_report(callback: CallbackQuery, state: FSMContext):
    date = datetime.datetime.now()

    await state.set_state(GetReport.select_month)
    await state.update_data(month=date.month, year=date.year)

    text = f"""Выберите месяц
{date.month:0>2}.{date.year:0>2}"""
    kb = get_select_month()

    await callback.message.edit_text(text=text, reply_markup=kb)


@router.callback_query(SelectMonth.filter(F.action != "confirm"), StateFilter(GetReport.select_month))
async def process(callback: CallbackQuery, callback_data: SelectMonth, state: FSMContext):
    data = await state.get_data()
    month = data.get("month")
    year = data.get("year")

    match callback_data.action:
        case ("update_month"):
            month = (month + callback_data.value) % 12 or 12
        case ("update_year"):
            year = year + callback_data.value
        case ("ignore"):
            await callback.answer()

    await state.update_data(month=month, year=year)

    text = f"""Выберите месяц
{month:0>2}.{year:0>2}"""
    kb = get_select_month()

    await callback.message.edit_text(text=text, reply_markup=kb)


@router.callback_query(SelectMonth.filter(F.action == "confirm"), StateFilter(GetReport.select_month))
async def get_report(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    month = data.get("month")
    year = data.get("year")
    try:
        path = await get_full_exel(year=year, month=month)
        await callback.message.delete()
        await callback.message.answer_document(FSInputFile(path))
        os.remove(path)
        await state.clear()
    except Exception as e:
        logger.error(e)
        await callback.message.edit_text("Произошла ошибка. Пожалуйста попробуйте ещё раз")
