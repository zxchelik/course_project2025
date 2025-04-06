import html
from contextlib import suppress
from datetime import datetime, date as date_type
from typing import Callable, Awaitable

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.database.db_cmd.cantainers_cmd import get_container_number_by_suffix_assembling, move_container
from src.backend.database.db_cmd.cassette_cmd import get_cassette_number_by_suffix_assembling
from src.backend.database.db_cmd.names_cmd import select_names
from src.backend.database.models import Cassette, AssemblyStep, User, Container
from src.backend.database.models.assembly_step import AssemblyStepTypes
from src.backend.database.models.blank_cassettes import CassetteType
from src.backend.database.models.cassette import CassetteState
from src.backend.database.modelsDTO.AssemblyInfo import AssemblyInfo
from src.backend.database.modelsDTO.cassette import AdditionalModel, CassetteAssembleModel
from src.backend.database.modelsDTO.container import ContainerModel
from src.backend.database.session_context import sessionmaker
from src.backend.telegram.keyboards.inline import get_inline_kb, get_confirm_date_ikb, get_confirm_ikb
from src.backend.telegram.states.users import CassetteAssembling
from src.backend.telegram.utils.aiogram_calendar import SimpleCalendar
from src.backend.telegram.utils.forward_report import forward_report, ReportType
from src.backend.telegram.utils.group_select import GroupSelector, GroupSelectorCallbackData, UserGroup

router = Router()


text1 = "Введите последние цифры кассеты"
text1e1 = lambda value: (
    'Не получилось считать число. Убедитесь, что вы ввели ТОЛЬКО число вида "01", "1", "41" и т.д\n'
    f'Вы ввели: "{value}"'
)
text1e2 = "Не получилось найти кассеты, с таким номером. Попробуй ещё раз."

text2 = "Выберите номер из списка или введите ещё раз последние цифры кассеты"
text3 = lambda date: f"Дата: {date.strftime('%d.%m.%Y')}"

text4 = "Введите последние цифры дополнения"
text4e2 = "Не получилось найти дополнения, с таким номером. Попробуй ещё раз."

text5 = "Введите последние цифры бочки"
text5e2 = "Не получилось найти бочку, с таким номером. Попробуй ещё раз."


# MARK: datepicker
onDateSelect = Callable[[CallbackQuery, FSMContext], Awaitable[None]]


async def start_date_select(callback: CallbackQuery, state: FSMContext, on_date_select: onDateSelect):
    await state.update_data(ods=on_date_select)
    await state.set_state(CassetteAssembling.select_date)
    date = datetime.today().date()
    kb = get_confirm_date_ikb()
    await state.update_data(date=date)
    await callback.message.edit_text(text=text3(date), reply_markup=kb)


@router.callback_query(Text(startswith="confirm"), StateFilter(CassetteAssembling.select_date))
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
            ods: onDateSelect = data.get("ods")
            await ods(callback, state)


@router.callback_query(StateFilter(CassetteAssembling.select_date))
async def process_select_date(callback: CallbackQuery, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback)
    if selected:
        await state.update_data(date=date)
        kb = get_confirm_date_ikb()
        await callback.message.answer(text=text3(date), reply_markup=kb)


# MARK: group_selector
onGroupSelect = Callable[[CallbackQuery, FSMContext], Awaitable[None]]


async def start_select_group(
    callback: CallbackQuery, state: FSMContext, is_help_enabled: bool, on_group_select: onGroupSelect
):
    await state.set_state(CassetteAssembling.select_group)
    group_selector = GroupSelector(user_id=callback.from_user.id, is_help_enabled=is_help_enabled)
    await group_selector.start(callback=callback)
    await state.update_data(group_selector=group_selector, ogs=on_group_select)


@router.callback_query(StateFilter(CassetteAssembling.select_group), GroupSelectorCallbackData.filter())
async def process_select_group(callback: CallbackQuery, callback_data: GroupSelectorCallbackData, state: FSMContext):
    data = await state.get_data()
    group_selector: GroupSelector = data.get("group_selector")
    if await group_selector.process(callback, callback_data):
        user_group = group_selector.get_result_dto()
        ogs: onGroupSelect = data.get("ogs")
        await state.update_data(user_group=user_group)
        await ogs(callback, state)


# MARK: start
@router.callback_query(Text("assemble_cassette"))
async def start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CassetteAssembling.select_cassette)
    await state.update_data(msg=callback.message)
    await callback.message.edit_text(text1)


# MARK: select_cassette
@router.message(StateFilter(CassetteAssembling.select_cassette))
async def process_select_cassette_number(message: Message, state: FSMContext):
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

    numbers = await get_cassette_number_by_suffix_assembling(suffix=value)
    if not numbers:
        with suppress(TelegramBadRequest):
            return await msg.edit_text(text1e2)

    kb = get_inline_kb([[(i, i)] for i in numbers])
    with suppress(TelegramBadRequest):
        await msg.edit_text(text=text2, reply_markup=kb)


@router.callback_query(StateFilter(CassetteAssembling.select_cassette), Text(startswith="confirm_"))
async def process_confirm_select_cassette_number(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split("_")[1]
    match value:
        case "cancel":
            data = await state.get_data()
            number_suffix = data.get("number_suffix")
            numbers = await get_cassette_number_by_suffix_assembling(suffix=number_suffix)
            if not numbers:
                return await callback.message.edit_text(text1e2)

            kb = get_inline_kb([[(i, i)] for i in numbers])
            with suppress(TelegramBadRequest):
                await callback.message.edit_text(text=text2, reply_markup=kb)
        case "confirm":
            await print_assemble_menu(callback, state)


@router.callback_query(StateFilter(CassetteAssembling.select_cassette))
async def start_confirm_select_cassette_number(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    number = callback.data
    cassette_db = (
        await db_session.scalars(
            select(Cassette)
            .filter(Cassette.number == number)
            .options(selectinload(Cassette.additions), selectinload(Cassette.containers))
        )
    ).one_or_none()
    cassette = CassetteAssembleModel.from_orm(cassette_db)
    ai = AssemblyInfo(cassette=cassette)

    await state.update_data(ai=ai)
    text = f"<pre>{cassette.to_str_table_view()}</pre>"
    kb = get_inline_kb(
        rows=[[("Изменить📝", "cancel"), ("Подтвердить✅", "confirm")]],
        prefix="confirm",
    )

    await callback.message.edit_text(text=text, reply_markup=kb)


# MARK: print_assemble_menu
async def print_assemble_menu(callback: CallbackQuery, state: FSMContext, *args, **kwargs):
    data = await state.get_data()
    ai: AssemblyInfo = data.get("ai")
    await state.clear()
    await state.set_state(CassetteAssembling.menu)
    await state.update_data(ai=ai)
    kb = get_inline_kb(
        rows=[
            [("Вставить бочку", "start_add_container")],
            [("Установить кран", "start_add_crane")],
            [("Установить доп", "start_addition_select")],
            [("Растворный узел", "start_add_dissolver_unit")],
        ]
    )
    cassette = ai.cassette
    await callback.message.edit_text(text=f"<pre>{cassette.to_str_table_view()}</pre>", reply_markup=kb)


# MARK: addition_select
@router.callback_query(StateFilter(CassetteAssembling.menu), Text("start_addition_select"))
async def start_addition_select(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CassetteAssembling.select_additional)
    await state.update_data(msg=callback.message)
    await callback.message.edit_text(text4)


@router.message(StateFilter(CassetteAssembling.select_additional))
async def process_select_additional_number(message: Message, state: FSMContext):
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

    numbers = await get_cassette_number_by_suffix_assembling(suffix=value, cassette_type=CassetteType.REMOVABLE)
    if not numbers:
        with suppress(TelegramBadRequest):
            return await msg.edit_text(text4e2)

    kb = get_inline_kb([[(i, i)] for i in numbers])
    with suppress(TelegramBadRequest):
        await msg.edit_text(text=text2, reply_markup=kb)


@router.callback_query(StateFilter(CassetteAssembling.select_additional), Text(startswith="confirm_"))
async def process_confirm_select_additional_number(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split("_")[1]
    match value:
        case "cancel":
            data = await state.get_data()
            number_suffix = data.get("number_suffix")
            numbers = await get_cassette_number_by_suffix_assembling(
                suffix=number_suffix, cassette_type=CassetteType.REMOVABLE
            )
            if not numbers:
                return await callback.message.edit_text(text4e2)

            kb = get_inline_kb([[(i, i)] for i in numbers])
            with suppress(TelegramBadRequest):
                await callback.message.edit_text(text=text2, reply_markup=kb)
        case "confirm":
            await start_date_select(callback, state, datepicker_group_selector_addition)


@router.callback_query(StateFilter(CassetteAssembling.select_additional))
async def start_confirm_select_additional_number(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    number = callback.data
    cassette_db = (await db_session.scalars(select(Cassette).filter(Cassette.number == number))).one_or_none()
    cassette = AdditionalModel.from_orm(cassette_db)

    await state.update_data(addition=cassette)
    text = f"<pre>{cassette.to_str_table_view()}</pre>"
    kb = get_inline_kb(
        rows=[[("Изменить📝", "cancel"), ("Подтвердить✅", "confirm")]],
        prefix="confirm",
    )

    await callback.message.edit_text(text=text, reply_markup=kb)


async def datepicker_group_selector_addition(callback: CallbackQuery, state: FSMContext):
    await start_select_group(callback, state, False, confirm_add_addition)


# MARK: confirm_add_addition
async def confirm_add_addition(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CassetteAssembling.confirm_select_additional)
    data = await state.get_data()
    ai: AssemblyInfo = data.get("ai")
    addition: AdditionalModel = data.get("addition")
    date: date_type = data.get("date")
    user_group: UserGroup = data.get("user_group")
    text = f"""Подтвердите действие
<pre>кассета:    {ai.cassette.number}
дополнение: {addition.number}
дата:       {date.strftime('%d.%m.%Y')}
группа:     {', '.join([i.fio for i in user_group.group])}</pre>
"""
    kb = get_confirm_ikb()
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(StateFilter(CassetteAssembling.confirm_select_additional))
async def process_confirm_add_addition(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    if callback.data == "confirm":
        data = await state.get_data()
        ai: AssemblyInfo = data.get("ai")
        cassette_dto = ai.cassette
        addition_dto: AdditionalModel = data.get("addition")
        date: date_type = data.get("date")
        user_group: UserGroup = data.get("user_group")
        cassette = await db_session.get(
            Cassette,
            cassette_dto.id,
            options=[
                selectinload(Cassette.additions),
                selectinload(Cassette.assembly_steps),
                selectinload(Cassette.containers),
            ],
        )
        addition = await db_session.get(Cassette, addition_dto.id)
        cassette.additions.append(addition)
        step = AssemblyStep(assemble_type=AssemblyStepTypes.ADDITION, assemble_date=date, component_id=addition.id)
        stmt = select(User).where(User.tg_id.in_([i.id for i in user_group.group]))
        users = (await db_session.execute(stmt)).scalars().all()
        step.users += users
        cassette.assembly_steps.append(step)
        addition.state = cassette.state
        await db_session.commit()
        await db_session.refresh(cassette)
        ai.cassette = CassetteAssembleModel.from_orm(cassette)
        await state.update_data(ai=ai)
        info_text = html.escape(
            f"""кассета:    {ai.cassette.number}
Доп:        {addition.number}
Наимен.:    {addition.name}
дата:       {date.strftime('%d.%m.%Y')}
группа:     {', '.join([i.fio for i in user_group.group])}"""
        )
        text = f"""#Дополнение\n<pre>{info_text}</pre>"""
        await forward_report(report_type=ReportType.ASSEMBLING, text=text)
    await print_assemble_menu(callback, state)


# MARK: add_crane
@router.callback_query(StateFilter(CassetteAssembling.menu), Text("start_add_crane"))
async def start_add_crane(callback: CallbackQuery, state: FSMContext):
    await start_date_select(callback, state, add_crane)


async def add_crane(callback: CallbackQuery, state: FSMContext):
    cranes = await select_names(parent_id=6)
    buttons = [[(i.name, i.name)] for i in cranes] + [[("Назад", "back")]]
    kb = get_inline_kb(rows=buttons)
    text = "Сделайте выбор"
    await state.set_state(CassetteAssembling.select_crane)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(StateFilter(CassetteAssembling.select_crane))
async def proces_add_crane(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    value = callback.data
    if value != "back":
        data = await state.get_data()
        ai: AssemblyInfo = data.get("ai")
        assemble_date = data.get("date")

        cassette = await db_session.get(
            Cassette,
            ai.cassette.id,
            options=[
                selectinload(Cassette.additions),
                selectinload(Cassette.assembly_steps),
                selectinload(Cassette.containers),
            ],
        )
        user = await db_session.get(User, callback.from_user.id)

        cassette.crane.append(value)
        step = AssemblyStep(assemble_type=AssemblyStepTypes.CRANE, assemble_date=assemble_date)
        step.users.append(user)
        cassette.assembly_steps.append(step)

        await db_session.commit()
        await db_session.refresh(cassette)
        ai.cassette = CassetteAssembleModel.from_orm(cassette)
        await state.update_data(ai=ai)
        info_text = html.escape(
            f"""кассета:    {ai.cassette.number}
кран:       {value}
дата:       {assemble_date.strftime('%d.%m.%Y')}
группа:     {user.fio}"""
        )
        text = f"""#Кран\n<pre>{info_text}</pre>"""
        await forward_report(report_type=ReportType.ASSEMBLING, text=text)
    await print_assemble_menu(callback, state)


# MARK: start_add_dissolver_unit
@router.callback_query(StateFilter(CassetteAssembling.menu), Text("start_add_dissolver_unit"))
async def start_add_dissolver_unit(callback: CallbackQuery, state: FSMContext):
    text = "Выберите"
    kb = get_inline_kb([[("Добавить Растворный узел", "add")], [("Назад", "back")]])
    await callback.message.edit_text(text, reply_markup=kb)
    await state.set_state(CassetteAssembling.select_dissolver_unit)


@router.callback_query(StateFilter(CassetteAssembling.select_dissolver_unit))
async def proces_add_dissolver_unit(callback: CallbackQuery, state: FSMContext):
    if callback.data == "back":
        await print_assemble_menu(callback, state)
        return
    await start_date_select(callback, state, datepicker_group_selector_du)


async def datepicker_group_selector_du(callback: CallbackQuery, state: FSMContext):
    await start_select_group(callback, state, False, add_dissolver_unit)


async def add_dissolver_unit(callback: CallbackQuery, state: FSMContext):
    async with sessionmaker() as session:
        data = await state.get_data()
        ai: AssemblyInfo = data.get("ai")
        assemble_date = data.get("date")
        user_group: UserGroup = data.get("user_group")
        du = Cassette(
            name=f"Растворный узел({ai.cassette.number})",
            state=ai.cassette.state,
            type=CassetteType.DISSOLVER_UNIT,
            cassette_id=ai.cassette.id,
            cut_date=date_type.today(),
            technical_comment="Заглушка",
        )
        session.add(du)

        stmt = select(User).where(User.tg_id.in_([i.id for i in user_group.group]))
        users = (await session.execute(stmt)).scalars().all()
        await session.flush()
        step = AssemblyStep(
            assemble_date=assemble_date,
            assemble_type=AssemblyStepTypes.DISSOLVER_UNIT,
            component_id=du.id,
            cassette_id=ai.cassette.id,
            users=users,
        )
        session.add(step)
        await session.commit()
        cassette = await session.get(
            Cassette, ai.cassette.id, options=[selectinload(Cassette.additions), selectinload(Cassette.containers)]
        )
        ai.cassette = CassetteAssembleModel.from_orm(cassette)
        await state.update_data(ai=ai)

        info_text = html.escape(
            f"""кассета:    {ai.cassette.number}
Р узел:     {du.name}
дата:       {assemble_date.strftime('%d.%m.%Y')}
группа:     {', '.join([i.fio for i in user_group.group])}"""
        )
        text = f"""#Растворный_узел\n<pre>{info_text}</pre>"""
        await forward_report(report_type=ReportType.ASSEMBLING, text=text)

    await print_assemble_menu(callback, state)


# MARK: start_add_container
@router.callback_query(StateFilter(CassetteAssembling.menu), Text("start_add_container"))
async def start_container_select(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CassetteAssembling.select_cont)
    await state.update_data(msg=callback.message)
    await callback.message.edit_text(text5)


@router.message(StateFilter(CassetteAssembling.select_cont))
async def process_select_container_number(message: Message, state: FSMContext):
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

    numbers = await get_container_number_by_suffix_assembling(suffix=value)
    if not numbers:
        with suppress(TelegramBadRequest):
            return await msg.edit_text(text5e2)

    kb = get_inline_kb([[(i, i)] for i in numbers])
    with suppress(TelegramBadRequest):
        await msg.edit_text(text=text2, reply_markup=kb)


@router.callback_query(StateFilter(CassetteAssembling.select_cont), Text(startswith="confirm_"))
async def process_confirm_select_container_number(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split("_")[1]
    match value:
        case "cancel":
            data = await state.get_data()
            number_suffix = data.get("number_suffix")
            numbers = await get_container_number_by_suffix_assembling(suffix=number_suffix)
            if not numbers:
                return await callback.message.edit_text(text5e2)

            kb = get_inline_kb([[(i, i)] for i in numbers])
            with suppress(TelegramBadRequest):
                await callback.message.edit_text(text=text2, reply_markup=kb)
        case "confirm":
            await start_date_select(callback, state, datepicker_group_selector_container)


@router.callback_query(StateFilter(CassetteAssembling.select_cont))
async def start_confirm_select_container_number(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    number = callback.data
    cassette_db = (await db_session.scalars(select(Container).filter(Container.number == number))).one_or_none()
    container = ContainerModel.from_orm(cassette_db)
    await state.update_data(container=container)
    text = f"<pre>\n{container.to_str_table_view()}</pre>"
    kb = get_inline_kb(
        rows=[[("Изменить📝", "cancel"), ("Подтвердить✅", "confirm")]],
        prefix="confirm",
    )

    await callback.message.edit_text(text=text, reply_markup=kb)


async def datepicker_group_selector_container(callback: CallbackQuery, state: FSMContext):
    await start_select_group(callback, state, False, confirm_add_container)


# MARK: confirm_add_container
async def confirm_add_container(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CassetteAssembling.confirm_select_cont)
    data = await state.get_data()
    ai: AssemblyInfo = data.get("ai")
    container: ContainerModel = data.get("container")
    date: date_type = data.get("date")
    user_group: UserGroup = data.get("user_group")
    text = f"""Подтвердите действие
<pre>кассета:    {ai.cassette.number}
бочка:      {container.number}
дата:       {date.strftime('%d.%m.%Y')}
группа:     {', '.join([i.fio for i in user_group.group])}</pre>
"""
    kb = get_confirm_ikb()
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(StateFilter(CassetteAssembling.confirm_select_cont))
async def process_confirm_add_container(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    if callback.data == "confirm":
        data = await state.get_data()
        ai: AssemblyInfo = data.get("ai")
        cassette_dto = ai.cassette
        container_dto: ContainerModel = data.get("container")
        date: date_type = data.get("date")
        user_group: UserGroup = data.get("user_group")
        cassette = await db_session.get(
            Cassette,
            cassette_dto.id,
            options=[
                selectinload(Cassette.additions),
                selectinload(Cassette.assembly_steps),
                selectinload(Cassette.containers),
            ],
        )
        container = await db_session.get(Container, container_dto.id)
        cassette.containers.append(container)
        cassette.state = CassetteState.ASSEMBLE
        if cassette.additions:
            for addition in cassette.additions:
                addition.state = CassetteState.ASSEMBLE
        step = AssemblyStep(assemble_type=AssemblyStepTypes.CONTAINER, assemble_date=date, component_id=container.id)
        stmt = select(User).where(User.tg_id.in_([i.id for i in user_group.group]))
        users = (await db_session.execute(stmt)).scalars().all()
        step.users += users
        await move_container(
            session=db_session,
            number=container.number,
            to_storage=cassette.number,
            reasons_for_moving="Сборка",
            user_id=users[0].tg_id,
        )
        cassette.assembly_steps.append(step)
        await db_session.commit()
        await db_session.refresh(cassette)
        ai.cassette = CassetteAssembleModel.from_orm(cassette)
        await state.update_data(ai=ai)

        info_text = html.escape(
            f"""кассета:    {ai.cassette.number}
бочка:      {container.number}
дата:       {date.strftime('%d.%m.%Y')}
группа:     {', '.join([i.fio for i in user_group.group])}"""
        )
        text = f"""#Бочка
<pre>{info_text}</pre>
"""
        await forward_report(report_type=ReportType.ASSEMBLING, text=text)
    await print_assemble_menu(callback, state)
