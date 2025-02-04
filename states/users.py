from aiogram.fsm.state import StatesGroup, State


class RegisterStates(StatesGroup):
    fio = State()
    birthday = State()
    confirm = State()


class AddContainer(StatesGroup):
    date = State()
    name = State()
    number = State()
    color = State()
    weigh = State()
    batch_number = State()
    cover_article = State()
    comments = State()
    group = State()
    confirm = State()
    add_cont_name = State()


class AddHourlyWork(StatesGroup):
    date = State()
    select_hourly_work = State()
    get_duration = State()
    get_comment = State()
    confirm = State()


class CassetteCutting(StatesGroup):
    select_blank_cassette = State()
    select_quantity = State()
    select_date = State()
    confirm = State()


class CassetteWelding(StatesGroup):
    select_cassette = State()
    select_quantity = State()
    select_additions = State()
    select_date = State()
    select_cont_number = State()
    select_group = State()
    confirm = State()


class CassettePainting(StatesGroup):
    select_cont_number = State()
    select_date = State()
    select_group = State()
    select_paint_types = State()
    confirm = State()
