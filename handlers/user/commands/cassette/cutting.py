from datetime import datetime, date as date_type
from typing import Callable

from aiogram import Router, Bot
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from aiogram_calendar import SimpleCalendar
from database.db_cmd.blank_cassetes_cmd import get_task_by_id, TaskModel, execute_task
from database.db_cmd.user_cmd import select_user, is_admin
from envfile import conf
from handlers.user.message.different import send_menu
from keyboards.cassete.cutting import get_select_blank_cassette_kb, SelectBlankCassette, get_select_quantity_kb, \
    SelectQuantity
from keyboards.inline import get_confirm_ikb, get_confirm_date_ikb
from states.users import CassetteCutting
from utils.forward_report import forward_report, ReportType

router = Router()

text1 = "Выберите заготовку"
text2 = lambda quantity: f"""Выберите количество:
{quantity} шт."""
text3 = lambda date: f"Дата: {date.strftime('%d.%m.%Y')}"
text4 = lambda date: f"""Выберите дату:
{date.strftime("%d.%m.%Y")}"""
text5: Callable[[TaskModel, int, date_type], str] = lambda task, quantity, date: (
        "‼️ПРОВЕРЬ ВСЁ ВНИМАТЕЛЬНО НА ОШИБКИ‼️\n" +
        full_info(task, quantity, date)
)
text6: Callable[[TaskModel, int, date_type,str], str] = lambda task, quantity, date, user_fio: (
        "🛠️Нарезаны детали:\n" +
        full_info(task, quantity, date)+
        f"\nОтветственный: {user_fio}"
)
full_info: Callable[[TaskModel, int, date_type], str] = lambda task, quantity, date: f"""<pre>
Наимен:{task.cassette_name}
Кол-во:{quantity}/{task.quantity}
Дата  :{date}
</pre>
"""


@router.callback_query(Text('start_cassette_cutting'))
async def start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CassetteCutting.select_blank_cassette)
    kb = await get_select_blank_cassette_kb(page=0)
    text = text1
    await callback.message.edit_text(text=text, reply_markup=kb)


@router.callback_query(StateFilter(CassetteCutting.select_blank_cassette), SelectBlankCassette.filter())
async def process_select_cassette(callback: CallbackQuery, callback_data: SelectBlankCassette, state: FSMContext):
    action = callback_data.action
    value = callback_data.value

    async def display_list(page: int):
        kb = await get_select_blank_cassette_kb(page=page)
        text = text1
        await callback.message.edit_text(text=text, reply_markup=kb)

    match action:
        case "ch_page":
            data: dict = await state.get_data()
            page = data.setdefault("page", 0)
            page += value
            await display_list(page=page)
            await state.update_data(page=page)
        case "select":
            task = await get_task_by_id(task_id=value)
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="Назад❌", callback_data=SelectBlankCassette(action="back").pack()),
                    InlineKeyboardButton(text="Подтвердить✅",
                                         callback_data=SelectBlankCassette(action="confirm").pack()),
                ]
            ])
            await callback.message.edit_text(text=f"<pre>{task.to_str_table_view()}</pre>", reply_markup=kb)
            await state.update_data(task=task)
        case "back":
            data: dict = await state.get_data()
            page = data.setdefault("page", 0)
            await display_list(page=page)
        case "confirm":
            await start_select_quantity(callback=callback, state=state)


async def start_select_quantity(callback: CallbackQuery, state: FSMContext):
    text = text2(1)
    kb = get_select_quantity_kb()
    await state.update_data(quantity=1)
    await state.set_state(CassetteCutting.select_quantity)
    await callback.message.edit_text(text=text, reply_markup=kb)


@router.callback_query(StateFilter(CassetteCutting.select_quantity), SelectQuantity.filter())
async def process_select_quantity(callback: CallbackQuery, callback_data: SelectQuantity, state: FSMContext):
    action = callback_data.action
    value = callback_data.value
    match action:
        case "upd":
            data = await state.get_data()
            old_quantity = data.setdefault('quantity', 1)
            quantity = value + old_quantity
            quantity = max(1, quantity)
            if quantity == old_quantity:
                await callback.answer()
                return
            await state.update_data(quantity=quantity)
            await callback.message.edit_text(text=text2(quantity), reply_markup=get_select_quantity_kb())
        case "confirm":
            await start_select_date(callback, state)


async def start_select_date(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CassetteCutting.select_date)
    date = datetime.today().date()
    kb = get_confirm_date_ikb(prefix="confirm")
    await state.update_data(date=date)
    await callback.message.edit_text(text=text3(date), reply_markup=kb)


@router.callback_query(Text(startswith="confirm"), StateFilter(CassetteCutting.select_date))
async def process_confirm_date(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split('_')[1]
    now_date = datetime.today()
    data = await state.get_data()
    date = data.setdefault("date", now_date)

    match action:
        case "cancel":
            text = text4(now_date)
            kb = await SimpleCalendar().start_calendar(year=date.year, month=date.month)
            await callback.message.edit_text(text=text, reply_markup=kb)

        case "confirm":
            await start_confirm_info(callback, state)


@router.callback_query(StateFilter(CassetteCutting.select_date))
async def process_select_date(callback: CallbackQuery, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback)
    if selected:
        await state.update_data(date=date)
        kb = get_confirm_date_ikb(prefix="confirm")
        await callback.message.answer(text=text3(date), reply_markup=kb)


async def start_confirm_info(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CassetteCutting.confirm)
    data: dict = await state.get_data()
    task: TaskModel = data.get('task')
    quantity: int = data.get('quantity')
    date: date_type = data.get('date')
    text = text5(task=task, quantity=quantity, date=date)
    kb = get_confirm_ikb(prefix="confirm")
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(StateFilter(CassetteCutting.confirm), Text(startswith="confirm"))
async def process_confirm_info(callback: CallbackQuery, state: FSMContext, bot: Bot):
    action = callback.data.split('_')[1]
    match action:
        case "cancel":
            await state.clear()
            await start(callback=callback, state=state)
            return
        case "confirm":
            data: dict = await state.get_data()
            task: TaskModel = data.get('task')
            quantity: int = data.get('quantity')
            date: date_type = data.get('date')

            await execute_task(task_id=task.id, quantity=quantity, worker_id=callback.from_user.id, cut_date=date)

            worker = await select_user(callback.from_user.id)
            text = text6(task=task, quantity=quantity, date=date,user_fio=worker.fio)
            # await bot.send_message(conf.bot.spam_id, text)
            await forward_report(report_type=ReportType.CUTTING,text=text)

            await state.clear()
            await callback.message.edit_text(full_info(task=task, quantity=quantity, date=date))
            await send_menu(callback.message, is_admin=await is_admin(tg_id=callback.from_user.id))
