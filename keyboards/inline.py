from typing import Optional

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_inline_kb(rows: list, prefix: str = '') -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if prefix != '':
        prefix += "_"

    for row in rows:
        row_ = []
        for button in row:
            if type(button) == tuple:
                text, call = button
                row_.append(InlineKeyboardButton(
                    text=text, callback_data=prefix + call))
            else:
                row_.append(InlineKeyboardButton(
                    text=button, callback_data=prefix + button))
        builder.row(*row_)
    return builder.as_markup()


def get_confirm_user_kb(id):
    confirm_new_user = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅Принять", callback_data=f"activate_{id}"),
                          InlineKeyboardButton(text="❌Отказать", callback_data=f"del_{id}")]])
    return confirm_new_user


def get_confirm_ikb(prefix: str = ''):
    if prefix != '':
        prefix += "_"
    confirm_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅Подтвердить", callback_data=prefix + "confirm"),
                          InlineKeyboardButton(text="❌Отказаться", callback_data=prefix + "cancel")]])
    return confirm_kb


def get_confirm_date_ikb(prefix: str = "confirm") -> InlineKeyboardMarkup:
    if prefix:
        prefix += "_"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Готово✅", callback_data=f"{prefix}confirm"),
            InlineKeyboardButton(text="Изменить📝", callback_data=f"{prefix}cancel"),
        ]
    ])


def menu_kb(is_admin: bool = False) -> InlineKeyboardMarkup:
    rows = []
    user_buttons = [
        [("Внести бочку", "add_container"), ("Почасовая работа", "add_hourly_work")],
        [('Кассеты', 'cassette_menu')]
    ]
    admin_buttons = [
        [("Добавить наименование", "add_name"), ("Получить отчёт", "get_report")],
        [("Изменить цены", "edit_name_price"), ("Журнал", "get_stats")],
        [("Рассылка", "mailing"), ("Список бочек", "get_availability")],
        [("Остатки пластика", "get_plastic_residue"), ("Задачи на кассеты", "add_cassette_task")],
        [("Обычное меню", "user_menu")]

    ]

    if is_admin:
        [rows.append(i) for i in admin_buttons]
    else:
        [rows.append(i) for i in user_buttons]

    return get_inline_kb(rows=rows)


class SelectNumber(CallbackData, prefix="SelectNumber"):
    action: str
    value: Optional[int | str]


# def get_select_number_fab(is_subnum=True):
def get_select_number_fab():
    builder = InlineKeyboardBuilder()

    builder.button(
        text="-1", callback_data=SelectNumber(action="update_group", value=-1))
    builder.button(text="Печка", callback_data=SelectNumber(action="ignore"))
    builder.button(
        text="+1", callback_data=SelectNumber(action="update_group", value=1))
    builder.button(
        text="-5", callback_data=SelectNumber(action="update_num", value=-5))
    builder.button(
        text="-1", callback_data=SelectNumber(action="update_num", value=-1))
    builder.button(text="Номер", callback_data=SelectNumber(action="ignore"))
    builder.button(
        text="+1", callback_data=SelectNumber(action="update_num", value=1))
    builder.button(
        text="+5", callback_data=SelectNumber(action="update_num", value=5))
    # if is_subnum:
    builder.button(text="A", callback_data=SelectNumber(
        action="update_subnum", value="A"))
    builder.button(text="B", callback_data=SelectNumber(
        action="update_subnum", value="B"))
    builder.button(text="C", callback_data=SelectNumber(
        action="update_subnum", value="C"))
    builder.button(text="D", callback_data=SelectNumber(
        action="update_subnum", value="D"))
    builder.button(text="Подтвердить",
                   callback_data=SelectNumber(action="confirm"))

    builder.adjust(3, 5, 4, 1)

    return builder.as_markup()


class SelectMonth(CallbackData, prefix="SelectMonth"):
    action: str
    value: Optional[int | str]


def get_select_month():
    builder = InlineKeyboardBuilder()

    builder.button(
        text="-5", callback_data=SelectMonth(action="update_month", value=-5))
    builder.button(
        text="-1", callback_data=SelectMonth(action="update_month", value=-1))
    builder.button(text="Месяц", callback_data=SelectMonth(action="ignore"))
    builder.button(
        text="+1", callback_data=SelectMonth(action="update_month", value=1))
    builder.button(
        text="+5", callback_data=SelectMonth(action="update_month", value=5))

    builder.button(
        text="-1", callback_data=SelectMonth(action="update_year", value=-1))
    builder.button(text="Год", callback_data=SelectMonth(action="ignore"))
    builder.button(
        text="+1", callback_data=SelectMonth(action="update_year", value=1))

    builder.button(text="Подтвердить",
                   callback_data=SelectMonth(action="confirm"))

    builder.adjust(5, 3)

    return builder.as_markup()


class SelectDuration(CallbackData, prefix="SelectDuration"):
    action: str
    value: Optional[int]


def get_select_duration_fab():
    builder = InlineKeyboardBuilder()

    builder.button(text='Часы', callback_data=SelectDuration(action='ignore'))
    builder.button(
        text='-3', callback_data=SelectDuration(action='update_hour', value=-3))
    builder.button(
        text='-2', callback_data=SelectDuration(action='update_hour', value=-2))
    builder.button(
        text='-1', callback_data=SelectDuration(action='update_hour', value=-1))
    builder.button(
        text='+1', callback_data=SelectDuration(action='update_hour', value=1))
    builder.button(
        text='+2', callback_data=SelectDuration(action='update_hour', value=2))
    builder.button(
        text='+3', callback_data=SelectDuration(action='update_hour', value=3))
    builder.button(
        text='Минуты', callback_data=SelectDuration(action='ignore'))
    builder.button(
        text='-15', callback_data=SelectDuration(action='update_min', value=-15))
    builder.button(
        text='-10', callback_data=SelectDuration(action='update_min', value=-10))
    builder.button(
        text='-5', callback_data=SelectDuration(action='update_min', value=-5))
    builder.button(
        text='+5', callback_data=SelectDuration(action='update_min', value=5))
    builder.button(
        text='+10', callback_data=SelectDuration(action='update_min', value=10))
    builder.button(
        text='+15', callback_data=SelectDuration(action='update_min', value=15))

    builder.button(text="Подтвердить",
                   callback_data=SelectDuration(action="confirm"))

    builder.adjust(1, 6, repeat=True)
    return builder.as_markup()
