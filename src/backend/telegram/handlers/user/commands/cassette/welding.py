from datetime import date as date_type
from datetime import datetime
from typing import Any

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter, Text
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.telegram.utils.aiogram_calendar import SimpleCalendar
from src.backend.database.db_cmd.Exceptions import AdditionNotFoundException
from src.backend.database.db_cmd.cassette_cmd import (
    get_last_cassette_number,
    validate_number,
    get_max_quantity_for_welding_by_hash,
    get_raw_tasks_for_welding_by_hash,
    activate_welding_work,
    deactivate_welding_work,
    finish_welding_work,
)
from src.backend.database.models import Cassette, CassetteGroupMember
from src.backend.database.models.blank_cassettes import CassetteType
from src.backend.database.models.cassette_group_member import CassetteGroupMemberType
from src.backend.database.modelsDTO.cassette import (
    CassetteNumberModel,
    WeldCassetteTaskModel,
    RawCassetteModel,
    CassetteModel,
)
from src.backend.database.modelsDTO.user import UserIdFioModel
from src.backend.telegram.keyboards.cassete.cutting import get_select_quantity_kb, SelectQuantity
from src.backend.telegram.keyboards.cassete.welding import (
    SelectCassette,
    get_select_blank_cassette_kb,
    get_select_welding_addition_kb,
    SelectAdditional,
    get_number_select_kb,
)
from src.backend.telegram.keyboards.inline import get_inline_kb, get_confirm_ikb, SelectNumber, get_confirm_date_ikb
from src.backend.telegram.states.users import CassetteWelding
from src.backend.telegram.utils.forward_report import forward_report, ReportType
from src.backend.telegram.utils.group_select import GroupSelector, GroupSelectorCallbackData

router = Router()

text1 = "Выберите нужное изделие"
text2 = (
    lambda quantity, max_quantity: f"""Выберите количество:
{quantity}/{max_quantity} шт."""
)
text3 = "Перейти к выбору дополнений"
text4 = "Выберите дополнение"
text5 = lambda date: f"Дата: {date.strftime('%d.%m.%Y')}"
text6 = (
    lambda number: f"""Выберите номер
{number}"""
)
text7 = (
    lambda number: f"""Изделие с таким номером уже существует
{number}"""
)


def text8(addition: str, selected: list[str], comment: str | None):
    res = ""
    if comment:
        res += f"Комментарий: {comment}\n\n"

    for i in selected:
        res += i + "\n"

    res += "📝" + addition
    return res


@router.callback_query(Text("weld_cassette"))
async def start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CassetteWelding.select_cassette)
    kb = await get_select_blank_cassette_kb(page=0)
    text = text1
    await callback.message.edit_text(text=text, reply_markup=kb)


@router.callback_query(StateFilter(CassetteWelding.select_cassette), SelectCassette.filter())
async def process_select_cassette(callback: CallbackQuery, callback_data: SelectCassette, state: FSMContext):
    action = callback_data.action
    value = callback_data.value

    async def display_list(page: int):
        kb = await get_select_blank_cassette_kb(page=page)
        text = text1
        await callback.message.edit_text(text=text, reply_markup=kb)

    match action:
        case "ch_page":
            value = int(value)
            data: dict = await state.get_data()
            page = data.setdefault("page", 0)
            page += value
            await display_list(page=page)
            await state.update_data(page=page)
        case "select":
            raw_task = await get_raw_tasks_for_welding_by_hash(task_hash=value)
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="Назад❌", callback_data=SelectCassette(action="back").pack()),
                        InlineKeyboardButton(
                            text="Подтвердить✅", callback_data=SelectCassette(action="confirm").pack()
                        ),
                    ]
                ]
            )
            await callback.message.edit_text(text=f"<pre>{raw_task.to_str_table_view()}</pre>", reply_markup=kb)
            await state.update_data(task_hash=value, raw_task=raw_task)
        case "back":
            data: dict = await state.get_data()
            page = data.setdefault("page", 0)
            await display_list(page=page)
        case "confirm":
            await state.update_data(page=0)
            task_hash = (await state.get_data()).get("task_hash")
            raw_task = await get_raw_tasks_for_welding_by_hash(task_hash=task_hash)
            match raw_task.type:
                case CassetteType.CASSETTE:
                    await start_select_additions(callback=callback, state=state)
                case CassetteType.REMOVABLE:
                    await start_select_date(callback=callback, state=state)


async def start_select_additions(callback: CallbackQuery, state: FSMContext):
    if (await state.get_data()).get("raw_task").type == CassetteType.REMOVABLE:
        return await start_select_date(callback=callback, state=state)
    data = await state.get_data()
    await state.set_state(CassetteWelding.select_additions)
    text = text3
    kb = get_inline_kb([[("Пропустить➡️", "skip"), ("Перейти✅", "goto")]], prefix="gotoaddition")
    await callback.message.edit_text(text3, reply_markup=kb)


@router.callback_query(StateFilter(CassetteWelding.select_additions), Text(startswith="gotoaddition"))
async def start_process_addition(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    match action:
        case "goto":
            text = text4
            kb = await get_select_welding_addition_kb(page=0)
            await callback.message.edit_text(text, reply_markup=kb)
        case "skip":
            await start_select_date(callback, state)


@router.callback_query(StateFilter(CassetteWelding.select_additions), SelectAdditional.filter())
async def process_select_additional(callback: CallbackQuery, callback_data: SelectAdditional, state: FSMContext):
    action = callback_data.action
    value = callback_data.value

    async def display_list(page: int):
        kb = await get_select_welding_addition_kb(page=page)
        text = text4
        await callback.message.edit_text(text=text, reply_markup=kb)

    data: dict = await state.get_data()
    match action:
        case "ch_page":
            page = data.setdefault("page", 0)
            page += int(value)
            await display_list(page=page)
            await state.update_data(page=page)
        case "select":
            addition = value
            addition_names = data.setdefault("addition_names", [])
            task: RawCassetteModel = data.get("raw_task")
            text = text8(addition=addition, selected=addition_names, comment=task.comment)
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="Изменить📝", callback_data=SelectAdditional(action="edit").pack()),
                        InlineKeyboardButton(
                            text="Добавить ещё➕", callback_data=SelectAdditional(action="add_more").pack()
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="Закончить✅", callback_data=SelectAdditional(action="confirm").pack()
                        ),
                    ],
                ]
            )
            await callback.message.edit_text(text=text, reply_markup=kb)
            addition_names.append(addition)
            await state.update_data(addition_names=addition_names)
        case "edit":
            addition_names = data.setdefault("addition_names", [])
            addition_names.pop()
            await state.update_data(addition_names=addition_names)
            page = data.setdefault("page", 0)
            await display_list(page=page)
        case "add_more":
            text = text4
            kb = await get_select_welding_addition_kb(page=0)
            await callback.message.edit_text(text, reply_markup=kb)

        case "confirm":
            await state.update_data(page=0)
            await start_select_date(callback=callback, state=state)


async def start_select_date(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CassetteWelding.select_date)
    date = datetime.today().date()
    kb = get_confirm_date_ikb()
    await state.update_data(date=date)
    await callback.message.edit_text(text=text5(date), reply_markup=kb)


@router.callback_query(Text(startswith="confirm"), StateFilter(CassetteWelding.select_date))
async def process_confirm_date(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    now_date = datetime.today()
    data = await state.get_data()
    date = data.setdefault("date", now_date)

    match action:
        case "cancel":
            text = text5(now_date)
            kb = await SimpleCalendar().start_calendar(year=date.year, month=date.month)
            await callback.message.edit_text(text=text, reply_markup=kb)

        case "confirm":
            await start_get_number(callback, state)


@router.callback_query(StateFilter(CassetteWelding.select_date))
async def process_select_date(callback: CallbackQuery, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback)
    if selected:
        await state.update_data(date=date)
        kb = get_confirm_date_ikb(prefix="confirm")
        await callback.message.answer(text=text5(date), reply_markup=kb)


async def start_get_number(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CassetteWelding.select_cont_number)

    data = await state.get_data()
    date: date_type = data.get("date")

    alf = [chr(i) for i in range(ord("А"), ord("Я") + 1) if i not in [ord(j) for j in "ЙЫËЪЬЩ"]]
    year_char = alf[(date.year - 2020) % len(alf)]

    number = CassetteNumberModel(
        year_char=year_char,
        group=1,
        month=date.month,
        number=await get_last_cassette_number(year_char=year_char, group=1, month=date.month),
    )

    await state.update_data(number=number)

    text = text6(number=number)
    kb = get_number_select_kb()
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(StateFilter(CassetteWelding.select_cont_number), SelectNumber.filter())
async def process_get_number(callback: CallbackQuery, callback_data: SelectNumber, state: FSMContext):
    action = callback_data.action
    value = callback_data.value
    data = await state.get_data()
    number: CassetteNumberModel = data.get("number")
    match action:
        case "update_group":
            number.update_group(value)

            number.set_number(
                await get_last_cassette_number(year_char=number.year_char, group=number.group, month=number.month)
            )
            text = text6(number=number)
            kb = get_number_select_kb()
            await callback.message.edit_text(text, reply_markup=kb)
        case "update_num":
            number.update_number(value)
            text = text6(number=number)
            kb = get_number_select_kb()
            await callback.message.edit_text(text, reply_markup=kb)
        case "ignore":
            return await callback.answer()
        case "confirm":
            if await validate_number(number=number):
                await start_select_group(callback, state)
            else:
                text = text7(number)
                kb = get_number_select_kb()
                try:
                    await callback.message.edit_text(text, reply_markup=kb)
                except TelegramBadRequest as e:
                    logger.error(e)


async def start_select_group(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CassetteWelding.select_group)
    group_selector = GroupSelector(user_id=callback.from_user.id)
    await group_selector.start(callback=callback)
    await state.update_data(group_selector=group_selector)


@router.callback_query(StateFilter(CassetteWelding.select_group), GroupSelectorCallbackData.filter())
async def process_select_group(callback: CallbackQuery, callback_data: GroupSelectorCallbackData, state: FSMContext):
    data = await state.get_data()
    group_selector: GroupSelector = data.get("group_selector")
    if await group_selector.process(callback, callback_data):
        group_users, help_group_users = group_selector.get_result()
        await state.update_data(group_users=group_users, help_group_users=help_group_users)
        await start_confirm(callback, state)
    await state.update_data(group_selector=group_selector)


def build_weld_cassette_task(fsm_data: dict[str, Any]) -> WeldCassetteTaskModel:
    task_hash = fsm_data.get("task_hash")
    task_quantity: int = fsm_data.setdefault("quantity", 1)

    raw_cassette: RawCassetteModel = fsm_data.get("raw_task")
    raw_additions = fsm_data.setdefault("addition_names", [])

    weld_date: date_type = fsm_data.get("date")
    number: CassetteNumberModel = fsm_data.get("number")
    group_users: list[UserIdFioModel] = fsm_data.get("group_users")
    help_group_users: list[UserIdFioModel] = fsm_data.get("help_group_users")

    numbers = [
        CassetteNumberModel(
            year_char=number.year_char,
            group=number.group,
            month=number.month,
            number=number.number + i,
        )
        for i in range(task_quantity)
    ]

    return WeldCassetteTaskModel(
        task_hash=task_hash,
        quantity=task_quantity,
        raw_cassette=raw_cassette,
        raw_additions=raw_additions,
        weld_date=weld_date,
        numbers=numbers,
        group=group_users,
        help_group=help_group_users,
    )


async def start_confirm(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CassetteWelding.confirm)

    data = await state.get_data()
    weld_cassette_task = build_weld_cassette_task(fsm_data=data)

    text = f"<pre>{weld_cassette_task.to_str_table_view()}</pre>"
    kb = get_confirm_ikb()
    kb.inline_keyboard.append(
        [InlineKeyboardButton(text="Внести несколько одинаковых", callback_data="select_quantity")]
    )
    await state.update_data(weld_cassette_task=weld_cassette_task)
    await callback.message.edit_text(text, reply_markup=kb)


class WeldCassette(CallbackData, prefix="WeldCassette"):
    action: str
    cassette_id: int


@router.callback_query(StateFilter(CassetteWelding.confirm))
async def process_confirm(callback: CallbackQuery, state: FSMContext):
    action = callback.data
    match action:
        case "cancel":
            await state.clear()
            await start(callback, state)
        case "confirm":
            wct: WeldCassetteTaskModel = (await state.get_data()).get("weld_cassette_task")
            # await callback.message.delete()
            for number in wct.numbers:
                if await validate_number(number=number):
                    try:
                        cassette = await activate_welding_work(task=wct, number=number)
                        cassette_model = CassetteModel.from_orm(cassette)
                        text = f"<pre>{cassette_model.to_str_table_view()}</pre>"
                        kb = InlineKeyboardMarkup(
                            inline_keyboard=[
                                [
                                    InlineKeyboardButton(
                                        text="Завершить✅",
                                        callback_data=WeldCassette(action="weld", cassette_id=cassette.id).pack(),
                                    ),
                                    InlineKeyboardButton(
                                        text="Отменить❌",
                                        callback_data=WeldCassette(
                                            action="cancel_welding", cassette_id=cassette.id
                                        ).pack(),
                                    ),
                                ]
                            ]
                        )
                        await callback.message.answer(text=text, reply_markup=kb)
                    except AdditionNotFoundException:
                        text = f"На изделие с номером: {number} не хватило дополнений на складе"  # TODO: change this
                        await callback.message.answer(text=text)
                else:
                    text = f"По моим данным уже существует изделие с номером: {number}"  # TODO: change this
                    await callback.message.answer(text=text)
            await state.clear()
        case "select_quantity":
            await start_select_quantity(callback, state)


async def start_select_quantity(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    max_quantity = await get_max_quantity_for_welding_by_hash(task_hash=data.get("task_hash"))
    text = text2(1, max_quantity)
    kb = get_select_quantity_kb()
    await state.update_data(quantity=1)
    await state.set_state(CassetteWelding.select_quantity)
    await callback.message.edit_text(text=text, reply_markup=kb)


@router.callback_query(StateFilter(CassetteWelding.select_quantity), SelectQuantity.filter())
async def process_select_quantity(callback: CallbackQuery, callback_data: SelectQuantity, state: FSMContext):
    action = callback_data.action
    value = callback_data.value
    match action:
        case "upd":
            data = await state.get_data()
            old_quantity = data.setdefault("quantity", 1)
            max_quantity = await get_max_quantity_for_welding_by_hash(task_hash=data.get("task_hash"))
            quantity = value + old_quantity

            quantity = max(1, quantity)
            quantity = min(max_quantity, quantity)

            if quantity == old_quantity:
                await callback.answer()
                return
            await state.update_data(quantity=quantity)
            await callback.message.edit_text(text=text2(quantity, max_quantity), reply_markup=get_select_quantity_kb())
        case "confirm":
            await start_confirm(callback, state)


@router.callback_query(WeldCassette.filter(F.action == "weld"))
async def weld_cassette(callback: CallbackQuery, callback_data: WeldCassette, bot: Bot, db_session: AsyncSession):
    text = f"Сварено✅\n<pre>{callback.message.text}</pre>"
    await finish_welding_work(cassette_id=callback_data.cassette_id)
    await callback.message.edit_text(text=text)
    cassette = await db_session.get(
        Cassette, callback_data.cassette_id, options=[selectinload(Cassette.groups), selectinload(Cassette.additions)]
    )
    additions = [i.name for i in cassette.additions]
    # noinspection PyTypeChecker
    groups: list[CassetteGroupMember] = cassette.groups
    group = [
        UserIdFioModel(id=i.user.tg_id, fio=i.user.fio)
        for i in groups
        if i.group_type == CassetteGroupMemberType.WELDER
    ]
    help_group = [
        UserIdFioModel(id=i.user.tg_id, fio=i.user.fio)
        for i in groups
        if i.group_type == CassetteGroupMemberType.WELDER_HELPER
    ]

    raw_cassette_model = RawCassetteModel.from_orm(cassette)
    model = WeldCassetteTaskModel(
        task_hash="",
        quantity=0,
        raw_cassette=raw_cassette_model,
        raw_additions=additions,
        weld_date=cassette.weld_date,
        numbers=[CassetteNumberModel.from_str(cassette.number)],
        group=group,
        help_group=help_group,
    )

    text = f"<pre>{model.to_str_table_view()}</pre>"
    # await bot.send_message(chat_id=conf.bot.spam_id, text=text)
    await forward_report(report_type=ReportType.WELDING, text=text)


@router.callback_query(WeldCassette.filter(F.action == "cancel_welding"))
async def cancel_cassette_welding(callback: CallbackQuery, callback_data: WeldCassette):
    text = f"Отменено❌\n<pre>{callback.message.text}</pre>"
    await deactivate_welding_work(cassette_id=callback_data.cassette_id)
    await callback.message.edit_text(text=text)
