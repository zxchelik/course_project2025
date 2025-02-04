from contextlib import suppress
from datetime import datetime

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram_calendar import SimpleCalendar
from database.db_cmd.cassette_cmd import get_cassette_number_by_suffix
from database.models import Cassette
from database.models.cassette import CassetteState
from database.modelsDTO.cassette import CassetteModel
from keyboards.inline import get_inline_kb, get_confirm_date_ikb
from states.users import CassettePainting
from utils.group_select import GroupSelector, GroupSelectorCallbackData

router = Router()

text1 = "Введите последние цифры изделия"
text1e1 = lambda value: (
    'Не получилось считать число. Убедитесь, что вы ввели ТОЛЬКО число вида "01", "1", "41" и т.д\n'
    f'Вы ввели: "{value}"'
)
text1e2 = "Не получилось найти непокрашенные касс" "еты, с таким номером. Попробуй ещё раз."

text2 = "Выберите номер из списка или введите ещё раз последние цифры изделия"
text3 = lambda date: f"Дата: {date.strftime('%d.%m.%Y')}"


@router.callback_query(Text("paint_cassette"))
async def start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CassettePainting.select_cont_number)
    await state.update_data(msg=callback.message)
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
        return await msg.edit_text(text1e1(value))

    await state.update_data(number_suffix=value)

    numbers = await get_cassette_number_by_suffix(suffix=value, cassette_state=CassetteState.WELDED)
    if not numbers:
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
            numbers = await get_cassette_number_by_suffix(suffix=number_suffix, cassette_state=CassetteState.WELDED)
            if not numbers:
                return await callback.message.edit_text(text1e2)

            kb = get_inline_kb([[(i, i)] for i in numbers])
            with suppress(TelegramBadRequest):
                await callback.message.edit_text(text=text2, reply_markup=kb)
        case "confirm":
            await start_select_date(callback, state)


@router.callback_query(StateFilter(CassettePainting.select_cont_number))
async def start_confirm_select_cont_number(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    number = callback.data
    cassette_db = (await db_session.scalars(select(Cassette).filter(Cassette.number == number))).one_or_none()
    cassette = CassetteModel.from_orm(cassette_db)
    await state.update_data(cassette=cassette)
    text = f"<pre>{cassette.to_str_table_view_welding()}</pre>"
    kb = (
        get_inline_kb(
            rows=[[("Изменить📝", "cancel"), ("Подтвердить✅", "confirm")]],
            prefix="confirm",
        ),
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
            await start_select_group(callback, state)


@router.callback_query(StateFilter(CassettePainting.select_date))
async def process_select_date(callback: CallbackQuery, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback)
    if selected:
        await state.update_data(date=date)
        kb = get_confirm_date_ikb(prefix="confirm")
        await callback.message.answer(text=text3(date), reply_markup=kb)


async def start_select_group(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CassettePainting.select_group)
    group_selector = GroupSelector(user_id=callback.from_user.id)
    await group_selector.start(callback=callback)
    await state.update_data(group_selector=group_selector)


@router.callback_query(StateFilter(CassettePainting.select_group), GroupSelectorCallbackData.filter())
async def process_select_group(callback: CallbackQuery, callback_data: GroupSelectorCallbackData, state: FSMContext):
    data = await state.get_data()
    group_selector: GroupSelector = data.get("group_selector")
    if await group_selector.process(callback, callback_data):
        group_users, help_group_users = group_selector.get_result()
        await state.update_data(group_users=group_users, help_group_users=help_group_users)
        await start_confirm(callback, state)
    await state.update_data(group_selector=group_selector)


# def build_paint_cassette_task(fsm_data: dict[str, Any]) -> WeldCassetteTaskModel:


async def start_confirm(callback: CallbackQuery, state: FSMContext): ...


# await state.set_state(CassettePainting.confirm)
#
# data = await state.get_data()
# weld_cassette_task = build_weld_cassette_task(fsm_data=data)
#
# text = f"<pre>{weld_cassette_task.to_str_table_view()}</pre>"
# kb = get_confirm_ikb()
