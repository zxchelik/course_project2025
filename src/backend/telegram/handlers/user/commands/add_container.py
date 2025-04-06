import datetime

from aiogram import Router, F
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from loguru import logger

from src.backend import misc
from src.backend.telegram.utils.aiogram_calendar import calendar_callback_filter, SimpleCalendar
from src.backend.database.db_cmd.cantainers_cmd import add_container, get_last_cont_numb, check_cont_numb
from src.backend.database.db_cmd.user_cmd import get_users, is_admin
from src.backend.telegram.filters.db_filters import CheckStatus
from src.backend.telegram.handlers.user.message.different import send_menu
from src.backend.telegram.keyboards.inline import get_inline_kb, get_confirm_ikb, get_select_number_fab, SelectNumber
from src.backend.telegram.keyboards.name_ikb import select_name_container_fub, SelectName, SelectGroup, select_group_fub
from src.backend.telegram.keyboards.reply import get_reply_keyboard
from src.backend.telegram.states.users import AddContainer
from src.backend.text_templates import *
from src.backend.telegram.utils.forward_report import forward_report, ReportType

router = Router()


@router.callback_query(CheckStatus("active"), Text("add_container"))
async def start_add_container(callback: CallbackQuery, state: FSMContext):
    now_date = datetime.date.today()
    await callback.message.edit_text(
        text=select_date, reply_markup=await SimpleCalendar().start_calendar(year=now_date.year, month=now_date.month)
    )
    await state.set_state(AddContainer.date)


@router.callback_query(calendar_callback_filter, StateFilter(AddContainer.date))
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


@router.callback_query(Text(startswith="confirm_"), StateFilter(AddContainer.date))
async def confirm_date(callback: CallbackQuery, state: FSMContext):
    update_code = callback.data.split("_")[1]
    if update_code == "cancel":
        await start_add_container(callback, state)
    elif update_code == "confirm":
        data = await state.get_data()
        date = data["date"]
        alf = [chr(i) for i in range(65, 91)]
        year_char = alf[(date.year - 2020) % 26]
        container_numb = [
            year_char,
            1,
            date.month,
            await get_last_cont_numb(year_char=year_char, furnace=1, month=date.month),
            "",
        ]
        await state.update_data(number=container_numb)

        text = select_numb.format(*container_numb[0:4], (container_numb[4] or " "))
        await callback.message.edit_text(text=text, reply_markup=get_select_number_fab())
        await state.set_state(AddContainer.number)


@router.callback_query(SelectNumber.filter(F.action != "confirm"), StateFilter(AddContainer.number))
async def get_number(callback: CallbackQuery, callback_data: SelectNumber, state: FSMContext):
    data = await state.get_data()
    container_numb: list = data.get("number")

    if callback_data.action == "update_group":
        container_numb[1] += callback_data.value
        container_numb[3] = await get_last_cont_numb(
            year_char=container_numb[0], furnace=container_numb[1], month=container_numb[2]
        )
    if callback_data.action == "update_num":
        container_numb[3] += callback_data.value
    if callback_data.action == "update_subnum":
        value = callback_data.value
        if value == container_numb[4]:
            container_numb[4] = ""
        else:
            container_numb[4] = value
    if callback_data.action == "ignore":
        return await callback.answer()

    await state.update_data(number=container_numb)
    text = select_numb.format(*container_numb)

    await callback.message.edit_text(text=text, reply_markup=get_select_number_fab())


@router.callback_query(SelectNumber.filter(F.action == "confirm"), StateFilter(AddContainer.number))
async def get_name(callback: CallbackQuery, callback_data: SelectNumber, state: FSMContext):
    data = await state.get_data()
    container_numb: list = data.get("number")
    if callback_data.action == "confirm":
        number = "{}{}.{}.{:0>3}{}".format(*container_numb)
        if await check_cont_numb(cont_number=number):
            await state.update_data(number=number)
            await state.set_state(AddContainer.name)
            text = select_name
            await callback.message.edit_text(text, reply_markup=await select_name_container_fub())
        else:
            text = select_numb_error.format(number=number)
            return await callback.message.edit_text(text=text, reply_markup=get_select_number_fab())


@router.callback_query(SelectName.filter(), StateFilter(AddContainer.name))
async def get_name_ikb(callback: CallbackQuery, callback_data: SelectName):
    page = callback_data.page
    parent_id = callback_data.parent_id
    await callback.message.edit_reply_markup(reply_markup=await select_name_container_fub(parent_id, page=page))


@router.callback_query(StateFilter(AddContainer.name))
async def get_color(callback: CallbackQuery, state: FSMContext):
    await state.update_data(name=callback.data)
    text = select_color
    await callback.message.edit_text(text)
    await state.update_data(msg=callback.message)
    await state.set_state(AddContainer.weigh)


@router.message(StateFilter(AddContainer.weigh))
async def get_weigh(message: Message, state: FSMContext):
    try:
        await message.delete()
        msg: Message = (await state.get_data()).get("msg")
        try:
            color = int(message.text)
        except ValueError:
            return await msg.edit_text(select_color_error)
        await state.update_data(color=color)
        text = select_weight
        await msg.edit_text(text)
        await state.set_state(AddContainer.batch_number)
    except Exception as e:
        logger.critical(e)
        await message.answer(
            "Что-то пошло не так. Введи значение еще раз.\n"
            " В случае, если значение не принимается несколько раз, начни ввод заново, нажав на /menu"
        )


@router.message(StateFilter(AddContainer.batch_number))
async def get_batch_number(message: Message, state: FSMContext):
    try:
        await message.delete()
        msg: Message = (await state.get_data()).get("msg")
        try:
            weigh = float(message.text)
        except ValueError:
            return await msg.edit_text(select_weight_error)
        await state.update_data(weigh=weigh)
        text = select_batch_number
        await msg.edit_text(text)
        await state.set_state(AddContainer.cover_article)
    except Exception as e:
        logger.critical(e)
        await message.answer(
            "Что-то пошло не так. Введи значение еще раз.\n"
            " В случае, если значение не принимается несколько раз, начни ввод заново, нажав на /menu"
        )


@router.message(StateFilter(AddContainer.cover_article))
async def get_cover_article(message: Message, state: FSMContext):
    try:
        await message.delete()
        msg: Message = (await state.get_data()).get("msg")
        try:
            batch_number = int(message.text)
        except ValueError:
            return await msg.edit_text(select_batch_number_error)
        await state.update_data(batch_number=batch_number)
        text = select_article
        await msg.edit_text(text)
        await state.set_state(AddContainer.comments)
    except Exception as e:
        logger.critical(e)
        await message.answer(
            "Что-то пошло не так. Введи значение еще раз.\n"
            " В случае, если значение не принимается несколько раз, начни ввод заново, нажав на /menu"
        )


@router.message(StateFilter(AddContainer.comments))
async def get_comments(message: Message, state: FSMContext):
    try:
        await message.delete()
        msg: Message = (await state.get_data()).get("msg")
        cover_article = message.text
        await state.update_data(cover_article=cover_article)
        text = get_comment
        await msg.delete()

        msg = await message.answer(text=text, reply_markup=get_reply_keyboard("Пропустить"))
        await state.update_data(msg=msg)

        await state.set_state(AddContainer.group)
    except Exception as e:
        logger.critical(e)
        await message.answer(
            "Что-то пошло не так. Введи значение еще раз.\n"
            " В случае, если значение не принимается несколько раз, начни ввод заново, нажав на /menu"
        )


@router.message(StateFilter(AddContainer.group))
async def get_group(message: Message, state: FSMContext):
    try:
        await message.delete()
        msg: Message = (await state.get_data()).get("msg")
        await msg.delete()
        data = await state.get_data()
        group = data.get("group", [message.from_user.id])

        mes = message.text
        if mes == "Пропустить":
            mes = ""
        await state.update_data(comments=mes)
        await state.update_data(group=group)

        text = select_group + f"\n{sep}".join(await get_users(users_id=group))
        await message.answer(text, reply_markup=await select_group_fub(user_id=message.from_user.id))

    except Exception as e:
        logger.critical(e)
        await message.answer(
            "Что-то пошло не так. Введи значение еще раз.\n"
            " В случае, если значение не принимается несколько раз, начни ввод заново, нажав на /menu"
        )


@router.callback_query(StateFilter(AddContainer.group), SelectGroup.filter(F.action != "confirm"))
async def select_page_group(callback: CallbackQuery, callback_data: SelectGroup, state: FSMContext):
    action = callback_data.action

    data = await state.get_data()
    group: list = data["group"]
    page = 0

    if action == "ch_page":
        page = callback_data.page
        data = await state.get_data()
        group = data.get("group")

    elif action == "upd":
        new_id = callback_data.id
        if new_id in group:
            group.remove(new_id)
        else:
            group.append(new_id)
        await state.update_data(group=group)

    text = select_group + f"\n{sep}".join(await get_users(users_id=group))

    await callback.message.edit_text(
        text, reply_markup=await select_group_fub(page=page, user_id=callback.from_user.id)
    )


@router.callback_query(StateFilter(AddContainer.group), SelectGroup.filter(F.action == "confirm"))
async def confirm(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddContainer.confirm)
    data = await state.get_data()
    info = [
        ["Дата", data["date"]],
        ["№ бочки", data["number"]],
        ["Наимен.", data["name"]],
        ["Цвет", data["color"]],
        ["Масса пл.", data["weigh"]],
        ["Партия пл.", data["batch_number"]],
        ["Арт. крыш.", data["cover_article"]],
        ["Бригада", f'\n{" " * 10}|'.join(await get_users(data["group"]))],
    ]

    main_header = f"""‼️ПРОВЕРЬ ВСЁ ВНИМАТЕЛЬНО НА ОШИБКИ‼️
{'-' * 10}+{'-' * 16}"""
    text = ""

    for disc, value in info:
        text += f"""
{disc: <10}|{value}
{'-' * 10}+{'-' * 16}"""
    text += f"""\nКоммент.: {data.get('comments')}"""
    kb = get_inline_kb(rows=[[("❌Начать заново", "cancel"), ("Всё верно ✅", "confirm")]], prefix="update")

    await state.update_data(info=text)
    await callback.message.edit_text(text=f"<pre>{main_header + text}</pre>", reply_markup=kb)


@router.callback_query(Text(startswith="update"), StateFilter(AddContainer.confirm))
async def get_confirm(callback: CallbackQuery, state: FSMContext):
    update_code = callback.data.split("_")[1]
    if update_code == "cancel":
        await state.clear()
        await start_add_container(callback, state)
    elif update_code == "confirm":
        data = await state.get_data()
        await add_container(
            date_cont=data["date"],
            number=data["number"],
            name=data["name"],
            color=data["color"],
            weight=data["weigh"],
            batch_number=data["batch_number"],
            cover_article=data["cover_article"],
            comments=data["comments"],
            users_id=data["group"],
        )

        info_text = data["info"]
        mailing_header = f"""Вас добавили напарником в
бригаду при выполнении работ:️
{'-' * 10}+{'-' * 16}"""
        for user in data["group"]:
            if user != callback.from_user.id:
                await misc.bot.send_message(user, f"<pre>{mailing_header + info_text}</pre>")
        header = f"{'-' * 10}+{'-' * 16}"
        # await misc.bot.send_message(conf.bot.spam_id, f'<pre>{header + info_text}</pre>')
        await forward_report(report_type=ReportType.CONTAINER, text=f"<pre>{header + info_text}</pre>")
        await callback.message.delete_reply_markup()

        await state.clear()
        await send_menu(callback.message, is_admin=await is_admin(tg_id=callback.from_user.id))
