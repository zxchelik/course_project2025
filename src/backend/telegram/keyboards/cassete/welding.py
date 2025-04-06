from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.backend.database.db_cmd.cassette_cmd import get_tasks_for_welding, get_unique_welding_addition_for_welding
from src.backend.database.modelsDTO.cassette import CassetteNQHModel
from src.backend.telegram.keyboards.inline import SelectNumber


class SelectCassette(CallbackData, prefix="SelectCassette"):
    action: str
    value: str | int | None


async def get_select_blank_cassette_kb(page: int, page_size: int = 10) -> InlineKeyboardMarkup:
    cassettes: list[CassetteNQHModel] = await get_tasks_for_welding()

    max_page = len(cassettes) // page_size + (len(cassettes) % page_size != 0) - 1
    cassettes = cassettes[page * page_size : (page + 1) * page_size]

    builder = InlineKeyboardBuilder()

    for i, cassette in enumerate(cassettes):
        builder.button(
            text=cassette.name + " - " + str(cassette.quantity),
            callback_data=SelectCassette(action="select", value=cassette.hash),
        )

    counter = 0
    if page > 0:
        builder.button(text="⬅️", callback_data=SelectCassette(action="ch_page", value=-1))
        counter += 1
    if page < max_page:
        builder.button(text="➡️", callback_data=SelectCassette(action="ch_page", value=1))
        counter += 1

    if counter != 0:
        builder.adjust(*[1 for _ in cassettes], counter)
    else:
        builder.adjust(*[1 for _ in cassettes])
    return builder.as_markup()


class SelectAdditional(SelectCassette, prefix="SelectAdditional"): ...


async def get_select_welding_addition_kb(page: int, page_size: int = 10) -> InlineKeyboardMarkup:
    additions = await get_unique_welding_addition_for_welding()

    max_page = len(additions) // page_size + (len(additions) % page_size != 0) - 1
    additions = additions[page * page_size : (page + 1) * page_size]

    builder = InlineKeyboardBuilder()

    for addition in additions:
        builder.button(text=addition[0], callback_data=SelectAdditional(action="select", value=addition[1]))

    counter = 0
    if page > 0:
        builder.button(text="⬅️", callback_data=SelectAdditional(action="ch_page", value=-1))
        counter += 1
    if page < max_page:
        builder.button(text="➡️", callback_data=SelectAdditional(action="ch_page", value=1))
        counter += 1
    builder.button(text="Не выбирать дополнение", callback_data="gotoaddition_skip")

    if counter != 0:
        builder.adjust(*[1 for _ in additions], counter, 1)
    else:
        builder.adjust(*[1 for _ in additions], 1)
    return builder.as_markup()


def get_number_select_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="-1", callback_data=SelectNumber(action="update_group", value=-1))
    builder.button(text="Бригада", callback_data=SelectNumber(action="ignore"))
    builder.button(text="+1", callback_data=SelectNumber(action="update_group", value=1))

    builder.button(text="-3", callback_data=SelectNumber(action="update_num", value=-3))
    builder.button(text="-1", callback_data=SelectNumber(action="update_num", value=-1))
    builder.button(text="Номер", callback_data=SelectNumber(action="ignore"))
    builder.button(text="+1", callback_data=SelectNumber(action="update_num", value=1))
    builder.button(text="+3", callback_data=SelectNumber(action="update_num", value=3))

    builder.button(text="Подтвердить", callback_data=SelectNumber(action="confirm"))

    builder.adjust(3, 5, 1)

    return builder.as_markup()
