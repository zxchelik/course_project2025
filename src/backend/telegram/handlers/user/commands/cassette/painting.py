from contextlib import suppress
from datetime import datetime

from aiogram import Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.telegram.utils.aiogram_calendar import SimpleCalendar
from src.backend.database.db_cmd.cassette_cmd import (
    get_cassette_number_by_suffix_painting,
    get_painting_states_by_id,
    paint_cassette,
)
from src.backend.database.db_cmd.user_cmd import is_admin, get_user
from src.backend.database.models import Cassette
from src.backend.database.modelsDTO.cassette import CassetteModelWithAdditions
from src.backend.database.modelsDTO.paint_task import PaintingTask
from src.backend.telegram.handlers.user.message.different import send_menu
from src.backend.telegram.keyboards.cassete.painting import PaintTypesSelector, PaintTypeSelectorCallbackData
from src.backend.telegram.keyboards.inline import get_inline_kb, get_confirm_date_ikb, get_confirm_ikb
from src.backend.telegram.states.users import CassettePainting
from src.backend.telegram.utils.forward_report import forward_report, ReportType

router = Router()

text1 = "Введите последние цифры изделия"
text1e1 = lambda value: (
    'Не получилось считать число. Убедитесь, что вы ввели ТОЛЬКО число вида "01", "1", "41" и т.д\n'
    f'Вы ввели: "{value}"'
)
text1e2 = "Не получилось найти непокрашенные кассеты, с таким номером. Попробуй ещё раз."

text2 = "Выберите номер из списка или введите ещё раз последние цифры изделия"
text3 = lambda date: f"Дата: {date.strftime('%d.%m.%Y')}"


@router.callback_query(Text("paint_cassette"))
async def start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CassettePainting.select_cont_number)
    await state.update_data(msg=callback.message)
    await state.update_data(pt=PaintingTask(user_id=callback.from_user.id))
    await callback.message.edit_text(text1)


@router.message(StateFilter(CassettePainting.select_cont_number))
async def process_select_cont_number(message: Message, state: FSMContext):
    value = message.text
    await message.delete()
    data = await state.get_data()
    msg: Message = data.get("msg")

    try:
        value = int(value)
    except ValueError:
        with suppress(TelegramBadRequest):
            return await msg.edit_text(text1e1(value))

    await state.update_data(number_suffix=value)

    numbers = await get_cassette_number_by_suffix_painting(suffix=value)
    if not numbers:
        with suppress(TelegramBadRequest):
            return await msg.edit_text(text1e2)

    kb = get_inline_kb([[(i, i)] for i in numbers])
    with suppress(TelegramBadRequest):
        await msg.edit_text(text=text2, reply_markup=kb)


@router.callback_query(StateFilter(CassettePainting.select_cont_number), Text(startswith="confirm_"))
async def process_confirm_select_cont_number(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split("_")[1]
    match value:
        case "cancel":
            data = await state.get_data()
            number_suffix = data.get("number_suffix")
            numbers = await get_cassette_number_by_suffix_painting(suffix=number_suffix)
            if not numbers:
                return await callback.message.edit_text(text1e2)

            kb = get_inline_kb([[(i, i)] for i in numbers])
            with suppress(TelegramBadRequest):
                await callback.message.edit_text(text=text2, reply_markup=kb)
        case "confirm":
            await start_select_date(callback, state)


@router.callback_query(StateFilter(CassettePainting.select_cont_number))
async def start_confirm_select_cont_number(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    data = await state.get_data()
    pt: PaintingTask = data.get("pt")

    number = callback.data
    cassette_db = (
        await db_session.scalars(
            select(Cassette).filter(Cassette.number == number).options(selectinload(Cassette.additions))
        )
    ).one_or_none()
    cassette = CassetteModelWithAdditions.from_orm(cassette_db)
    pt.cassette = cassette

    await state.update_data(pt=pt)
    text = f"<pre>{cassette.to_str_table_view()}</pre>"
    kb = get_inline_kb(
        rows=[[("Изменить📝", "cancel"), ("Подтвердить✅", "confirm")]],
        prefix="confirm",
    )

    await callback.message.edit_text(text=text, reply_markup=kb)


async def start_select_date(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CassettePainting.select_date)
    date = datetime.today().date()
    kb = get_confirm_date_ikb()
    await state.update_data(date=date)
    await callback.message.edit_text(text=text3(date), reply_markup=kb)


@router.callback_query(Text(startswith="confirm"), StateFilter(CassettePainting.select_date))
async def process_confirm_date(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    now_date = datetime.today()
    data = await state.get_data()
    date = data.setdefault("date", now_date)

    match action:
        case "cancel":
            text = text3(now_date)
            kb = await SimpleCalendar().start_calendar(year=date.year, month=date.month)
            await callback.message.edit_text(text=text, reply_markup=kb)

        case "confirm":
            pt: PaintingTask = data.get("pt")
            pt.painting_date = date
            await state.update_data(pt=pt)
            await start_select_types(callback, state)


@router.callback_query(StateFilter(CassettePainting.select_date))
async def process_select_date(callback: CallbackQuery, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback)
    if selected:
        await state.update_data(date=date)
        kb = get_confirm_date_ikb(prefix="confirm")
        await callback.message.answer(text=text3(date), reply_markup=kb)


async def start_select_types(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    pt: PaintingTask = data.get("pt")
    type_selector = PaintTypesSelector(locked_types=await get_painting_states_by_id(cassette_id=pt.cassette.id))
    await type_selector.start(callback)
    await state.update_data(type_selector=type_selector)
    await state.set_state(CassettePainting.select_paint_types)


@router.callback_query(StateFilter(CassettePainting.select_paint_types), PaintTypeSelectorCallbackData.filter())
async def process_select_types(
    callback: CallbackQuery, callback_data: PaintTypeSelectorCallbackData, state: FSMContext
):
    data = await state.get_data()
    type_selector: PaintTypesSelector = data.get("type_selector")
    _, res, is_finished = await type_selector.process(callback=callback, callback_data=callback_data)
    if _:
        if res:
            pt: PaintingTask = data.get("pt")
            pt.types = res
            pt.is_finished = is_finished
            await state.update_data(pt=pt)
            await start_confirm(callback, state)
        else:
            await callback.answer("‼️Нужно выбрать хотя бы 1 этап‼️", show_alert=True)


async def start_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    pt: PaintingTask = data.get("pt")
    text = str(pt)
    kb = get_confirm_ikb(prefix="confirm")
    await callback.message.edit_text(text, reply_markup=kb)
    await state.set_state(CassettePainting.confirm)


@router.callback_query(StateFilter(CassettePainting.confirm), Text(startswith="confirm"))
async def process_confirm_info(callback: CallbackQuery, state: FSMContext, bot: Bot):
    action = callback.data.split("_")[1]
    match action:
        case "cancel":
            await state.clear()
            await start(callback=callback, state=state)
            return
        case "confirm":
            data = await state.get_data()
            pt: PaintingTask = data.get("pt")
            await paint_cassette(task=pt)

    forward_text = f"<pre>{callback.message.text}\nМаляр: {(await get_user(user_id=callback.from_user.id)).fio}</pre>"

    await forward_report(report_type=ReportType.PAINTING, text=forward_text)

    await state.clear()
    await callback.message.delete_reply_markup()
    await send_menu(callback.message, is_admin=await is_admin(tg_id=callback.from_user.id))
