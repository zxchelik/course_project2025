from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db_cmd.blank_cassetes_cmd import get_tasks, TaskModel


class SelectBlankCassette(CallbackData, prefix="SelectBlankCassette"):
    action: str
    value: int | None


async def get_select_blank_cassette_kb(page: int, page_size: int = 10) -> InlineKeyboardMarkup:
    all_blank_cassettes: list[TaskModel] = await get_tasks()

    total_pages = len(all_blank_cassettes) // page_size + (len(all_blank_cassettes) % page_size != 0) - 1
    blank_cassettes = all_blank_cassettes[page * page_size : (page + 1) * page_size]

    builder = InlineKeyboardBuilder()

    for i, cassette in enumerate(blank_cassettes):
        builder.button(
            text=cassette.cassette_name + " - " + str(cassette.quantity),
            callback_data=SelectBlankCassette(action="select", value=cassette.id),
        )

    counter = 0
    if page > 0:
        builder.button(text="⬅️", callback_data=SelectBlankCassette(action="ch_page", value=-1))
        counter += 1
    if page < total_pages:
        builder.button(text="➡️", callback_data=SelectBlankCassette(action="ch_page", value=1))
        counter += 1

    if counter != 0:
        builder.adjust(*[1 for _ in blank_cassettes], counter)
    else:
        builder.adjust(*[1 for _ in blank_cassettes])
    return builder.as_markup()


class SelectQuantity(CallbackData, prefix="SelectQuantity"):
    action: str
    value: int | None


def get_select_quantity_kb() -> InlineKeyboardMarkup:
    values = [1, 2, 3]
    builder = InlineKeyboardBuilder()
    [builder.button(text=f"-{i}", callback_data=SelectQuantity(action="upd", value=-i)) for i in values[::-1]]
    [builder.button(text=f"+{i}", callback_data=SelectQuantity(action="upd", value=i)) for i in values]
    builder.button(text="Завершить", callback_data=SelectQuantity(action="confirm"))
    builder.adjust(len(values) * 2, 1)
    return builder.as_markup()
