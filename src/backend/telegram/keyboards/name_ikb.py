from typing import Union, Optional

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.backend.database.db_cmd.names_cmd import select_names, get_parent_id, select_name
from src.backend.database.db_cmd.user_cmd import select_all_users


class SelectName(CallbackData, prefix="SelectName"):
    page: int
    parent_id: Union[int, None]


class SelectGroup(CallbackData, prefix="SelectGroup"):
    action: str
    page: Optional[int]
    id: Optional[int]


async def get_full_name(id):
    ful_name = ""
    for i in range(2):
        name = await select_name(id=id)
        ful_name = f"{name.name}-" + ful_name
        id = await get_parent_id(id=id)
    return ful_name[:-1]


async def select_name_pattern(
    parent_id: Union[int, None] = -1,
    page: int = 0,
    page_size: int = 5,
    base: Union[int, None] = None,
    can_edit: bool = False,
):
    if parent_id == -1:
        parent_id = base
    _names = await select_names(parent_id=parent_id)
    names = _names[page * page_size : (page + 1) * page_size]
    builder = InlineKeyboardBuilder()
    total_pages = len(_names) // page_size - (len(_names) % page_size == 0)

    if _names:
        for name in names:
            builder.row(
                InlineKeyboardButton(text=name.name, callback_data=SelectName(page=0, parent_id=name.id).pack())
            )

        if page == total_pages and can_edit:
            builder.row(
                InlineKeyboardButton(text="✏️Добавить", callback_data=f"add_{parent_id}"),
                InlineKeyboardButton(text="✅Закончить", callback_data=f"finish"),
            )

        row = []
        if page != 0:
            row.append(
                InlineKeyboardButton(text="⬅️", callback_data=SelectName(page=page - 1, parent_id=parent_id).pack())
            )

        if parent_id != base:
            row.append(
                InlineKeyboardButton(
                    text="⏪Назад", callback_data=SelectName(page=0, parent_id=await get_parent_id(parent_id)).pack()
                )
            )

        if page < total_pages:
            row.append(
                InlineKeyboardButton(text="➡️", callback_data=SelectName(page=page + 1, parent_id=parent_id).pack())
            )

        builder.row(*row)

    elif (not _names) and (not can_edit):
        if base == 1:
            name = await get_full_name(parent_id)
        else:
            name = (await select_name(id=parent_id)).name
        builder.row(InlineKeyboardButton(text="✅ " + name, callback_data=name))
        if parent_id:
            builder.add(
                InlineKeyboardButton(
                    text="⏪Назад", callback_data=SelectName(page=0, parent_id=await get_parent_id(parent_id)).pack()
                )
            )

    elif (not _names) and can_edit:
        builder.row(
            InlineKeyboardButton(text="✏️Добавить", callback_data=f"add_{parent_id}"),
            InlineKeyboardButton(text="✅Закончить", callback_data=f"finish"),
        )

        row = []
        if parent_id != base:
            builder.row(
                InlineKeyboardButton(
                    text="⏪Назад", callback_data=SelectName(page=0, parent_id=await get_parent_id(parent_id)).pack()
                )
            )

    return builder.as_markup()


async def select_many_names_pattern(
    base: int | None, parent_id: int | None, selected_list: list[int] | None = None, page: int = 0, page_size: int = 5
) -> InlineKeyboardMarkup:
    if parent_id == -1:
        parent_id = base
    names_ = await select_names(parent_id=parent_id)
    names = names_[page * page_size : (page + 1) * page_size]
    total_pages = len(names_) // page_size - (len(names_) % page_size == 0)
    if selected_list is None:
        selected_list = []

    builder = InlineKeyboardBuilder()

    if names:
        for name in names:
            prefix = ""
            if name.id in selected_list:
                prefix = "✅"
            builder.row(
                InlineKeyboardButton(
                    text=prefix + name.name, callback_data=SelectName(page=0, parent_id=name.id).pack()
                )
            )

        row = []
        if page != 0:
            row.append(
                InlineKeyboardButton(text="⬅️", callback_data=SelectName(page=page - 1, parent_id=parent_id).pack())
            )

        if parent_id != base:
            row.append(
                InlineKeyboardButton(
                    text="⏪Назад", callback_data=SelectName(page=0, parent_id=await get_parent_id(parent_id)).pack()
                )
            )

        if page < total_pages:
            row.append(
                InlineKeyboardButton(text="➡️", callback_data=SelectName(page=page + 1, parent_id=parent_id).pack())
            )

        builder.row(*row)
    else:
        name = await select_name(id=parent_id)
        builder.row(InlineKeyboardButton(text="✅ " + name.name, callback_data=name.id))
        if parent_id:
            builder.add(
                InlineKeyboardButton(
                    text="⏪Назад", callback_data=SelectName(page=0, parent_id=await get_parent_id(parent_id)).pack()
                )
            )
    return builder.as_markup()


async def select_name_container_fub(parent_id: Union[int, None] = -1, page: int = 0, page_size: int = 5):
    return await select_name_pattern(base=1, parent_id=parent_id, page=page, page_size=page_size)


async def select_name_cassette_fub(parent_id: Union[int, None] = -1, page: int = 0, page_size: int = 5):
    return await select_name_pattern(base=2, parent_id=parent_id, page=page, page_size=page_size)


async def select_name_additional_fub(
    selected_list: list[int] | None = None, parent_id: Union[int, None] = -1, page: int = 0, page_size: int = 5
):
    return await select_many_names_pattern(
        base=3, parent_id=parent_id, page=page, page_size=page_size, selected_list=selected_list
    )


async def select_name_hourly_fub(
    selected_list: Union[list[int], None] = None, parent_id: Union[int, None] = -1, page: int = 0, page_size: int = 5
):
    return await select_many_names_pattern(
        base=4, parent_id=parent_id, page=page, page_size=page_size, selected_list=selected_list
    )


async def edit_name_fub(parent_id: Union[int, None] = -1, page: int = 0, page_size: int = 5):
    return await select_name_pattern(base=None, parent_id=parent_id, page=page, page_size=page_size, can_edit=True)


async def select_group_fub(
    user_id: int,
    page: int = 0,
    page_size: int = 5,
):
    users = list(await select_all_users(admin=False))
    total_pages = len(users) // page_size - (len(users) % page_size == 0)

    for user in users:
        if user.tg_id == user_id:
            users.remove(user)
        # if user.status == "deactive":
        #     users.remove(user)

    names = users[page * page_size : (page + 1) * page_size]
    builder = InlineKeyboardBuilder()

    for name in names:
        builder.button(text=name.fio, callback_data=SelectGroup(action="upd", id=int(name.tg_id)))

    counter = 0
    if page > 0:
        builder.button(text="⬅️", callback_data=SelectGroup(page=page - 1, action="ch_page"))
        counter += 1
    if page < total_pages:
        builder.button(text="➡️", callback_data=SelectGroup(page=page + 1, action="ch_page"))
        counter += 1

    builder.button(text="✅Закончить", callback_data=SelectGroup(action="confirm"))

    if counter != 0:
        builder.adjust(*[1 for i in names], counter, 1)
    else:
        builder.adjust(*[1 for i in names], 1)
    return builder.as_markup()
