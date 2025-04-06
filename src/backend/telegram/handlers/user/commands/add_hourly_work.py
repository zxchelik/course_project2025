import datetime
from datetime import date
from typing import Union

from aiogram import Router, F
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.backend.telegram.utils.aiogram_calendar import SimpleCalendar, calendar_callback_filter
from src.backend.database.db_cmd.hourly_work_cmd import add_hourly_work
from src.backend.database.db_cmd.names_cmd import select_name
from src.backend.database.db_cmd.user_cmd import is_admin, select_user
from src.backend.telegram.filters.db_filters import CheckStatus
from src.backend.telegram.handlers.user.message.different import send_menu
from src.backend.telegram.keyboards.inline import (
    get_confirm_ikb,
    get_select_duration_fab,
    SelectDuration,
    get_inline_kb,
)
from src.backend.telegram.keyboards.name_ikb import select_name_hourly_fub, SelectName
from src.backend.telegram.keyboards.reply import get_reply_keyboard
from src.backend.telegram.states.users import AddHourlyWork
from src.backend.text_templates import (
    select_date,
    confirm_date_text,
    select_name_text,
    select_duration,
    get_comment,
    invalid_date,
)
from src.backend.telegram.utils.forward_report import forward_report, ReportType

router = Router()


@router.callback_query(CheckStatus("active"), Text("add_hourly_work"))
async def start_add_hourly(callback: CallbackQuery, state: FSMContext):
    now_date = date.today()
    await callback.message.edit_text(
        text=select_date, reply_markup=await SimpleCalendar().start_calendar(year=now_date.year, month=now_date.month)
    )
    await state.set_state(AddHourlyWork.date)


@router.callback_query(calendar_callback_filter, StateFilter(AddHourlyWork.date))
async def process_simple_calendar(callback_query: CallbackQuery, state: FSMContext):
    selected, date_ = await SimpleCalendar().process_selection(callback_query)
    if selected:
        await state.update_data(date=date_)
        if (datetime.date.today() - date_).days < 2:
            await callback_query.message.answer(
                confirm_date_text.format(date=date_.strftime("%d.%m.%Y")),
                reply_markup=get_confirm_ikb(prefix="confirm"),
            )
        else:
            await callback_query.message.answer(
                invalid_date, reply_markup=get_inline_kb([[("Выбрать другую дату", "cancel")]], prefix="confirm")
            )


@router.callback_query(Text(startswith="confirm_"), StateFilter(AddHourlyWork.date))
async def confirm_date(callback: CallbackQuery, state: FSMContext):
    update_code = callback.data.split("_")[1]
    if update_code == "cancel":
        await start_add_hourly(callback, state)
    elif update_code == "confirm":
        await state.set_state(AddHourlyWork.select_hourly_work)
        await callback.message.edit_text(select_name_text, reply_markup=await select_name_hourly_fub())


@router.callback_query(SelectName.filter(), StateFilter(AddHourlyWork.select_hourly_work))
async def get_name_ikb(callback: CallbackQuery, callback_data: SelectName, state: FSMContext):
    page = callback_data.page
    parent_id = callback_data.parent_id
    data = await state.get_data()
    selected_list: Union[list[int], None] = data.get("selected_list", None)
    await callback.message.edit_reply_markup(
        reply_markup=await select_name_hourly_fub(parent_id=parent_id, selected_list=selected_list, page=page)
    )


@router.callback_query(StateFilter(AddHourlyWork.select_hourly_work))
async def get_color(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_list: list[int] = data.get("selected_list", [])
    selected_list.append(int(callback.data))
    await state.update_data(selected_list=selected_list)
    await state.set_state(AddHourlyWork.get_duration)
    text = select_duration.format(hour=1, min_=0)
    await callback.message.edit_text(text, reply_markup=get_select_duration_fab())


@router.callback_query(SelectDuration.filter(F.action != "confirm"), StateFilter(AddHourlyWork.get_duration))
async def get_duration(callback: CallbackQuery, callback_data: SelectDuration, state: FSMContext):
    data = await state.get_data()
    hour, minute = data.get("duration", [1, 0])
    action = callback_data.action

    match action:
        case "update_hour":
            hour += callback_data.value
        case "update_min":
            minute += callback_data.value
            if minute < 0:
                minute += 60
                hour -= 1
            elif minute >= 60:
                minute -= 60
                hour += 1
        case "ignore":
            return await callback.answer()
    await state.update_data(duration=[hour, minute])

    text = select_duration.format(hour=hour, min_=minute)

    await callback.message.edit_text(text, reply_markup=get_select_duration_fab())


@router.callback_query(SelectDuration.filter(F.action == "confirm"), StateFilter(AddHourlyWork.get_duration))
async def confirm_duration(callback: CallbackQuery, callback_data: SelectDuration, state: FSMContext):
    data = await state.get_data()
    hour, minute = data.get("duration", [1, 0])
    duration_list = data.get("duration_list", [])

    duration_list.append([hour, minute])
    await state.update_data(duration_list=duration_list)

    text = get_comment
    await callback.message.delete()

    msg = await callback.message.answer(text=text, reply_markup=get_reply_keyboard("Пропустить"))
    await state.update_data(msg=msg)

    await state.update_data(duration=[1, 0])
    await state.set_state(AddHourlyWork.get_comment)


@router.message(StateFilter(AddHourlyWork.get_comment))
async def get_comments(message: Message, state: FSMContext):
    comment = message.text

    if comment == "Пропустить":
        comment = None

    data = await state.get_data()
    comments = data.get("comments", [])
    comments.append(comment)
    await state.update_data(comments=comments)

    duration_list = data.get("duration_list", [])
    selected_list: list[int] = data.get("selected_list")

    text = f"Ты выбрал:\n{data.get('date')}"
    info = ""
    for name_id, duration, comment in zip(selected_list, duration_list, comments):
        h, m = duration
        name = (await select_name(name_id)).name
        info += f"\n<pre>{name} - {h:0>2}:{m:0>2}"
        if comment is not None:
            info += f"\nКомментарий: {comment}"
        info += "</pre>"
    text += info
    kb = get_inline_kb([[("✏️Добавить ещё за эту дату", "add"), ("✅Закончить", "finish")]])

    await message.delete()
    msg: Message = (await state.get_data()).get("msg")
    await msg.delete()

    await message.answer(text, reply_markup=kb)
    await state.update_data(info=info)
    await state.set_state(AddHourlyWork.confirm)


@router.callback_query(StateFilter(AddHourlyWork.confirm))
async def confirm(callback: CallbackQuery, state: FSMContext):
    callback_data = callback.data
    match callback_data:
        case "finish":
            data = await state.get_data()
            duration_list = data.get("duration_list")
            selected_list: list[int] = data.get("selected_list")
            comments: list[str | None] = data.get("comments")
            date_ = data.get("date")
            user_id = callback.from_user.id

            for name_id, duration, comment in zip(selected_list, duration_list, comments):
                h, m = duration
                name = (await select_name(name_id)).name
                duration = round((h * 60 + m) / 60, 3)
                await add_hourly_work(user_id=user_id, name=name, duration=duration, date_=date_, comment=comment)

            info = data.get("info")
            user = await select_user(tg_id=callback.from_user.id)
            info_text = f"{user.fio}\n{date_}\n{info}"
            # await misc.bot.send_message(conf.bot.spam_id, info_text)
            await forward_report(report_type=ReportType.HOURLY_WORK, text=info_text)

            await state.clear()
            await callback.message.delete_reply_markup()
            await send_menu(callback.message, is_admin=await is_admin(tg_id=callback.from_user.id))
        case "add":
            await state.set_state(AddHourlyWork.select_hourly_work)
            await callback.message.edit_text(select_name_text, reply_markup=await select_name_hourly_fub())
