from aiogram.fsm.state import StatesGroup, State


class GetDescription(StatesGroup):
    get_description = State()


class GetGroup(StatesGroup):
    get_group = State()


class AddName(StatesGroup):
    select_page = State()
    add_name = State()


class GetReport(StatesGroup):
    select_month = State()


class UpdateNames(StatesGroup):
    update_names = State()


class GetStats(StatesGroup):
    select_type_statistics = State()
    get_first_date = State()
    get_last_date = State()


class Mailing(StatesGroup):
    get_mailing = State()
    get_confirmed = State()


class GetAvailability(StatesGroup):
    select_type = State()
    get_file = State()


class GetPlasticResidue(StatesGroup):
    select_type = State()
    get_file = State()


class AddCassetteTask(StatesGroup):
    input_file = State()
