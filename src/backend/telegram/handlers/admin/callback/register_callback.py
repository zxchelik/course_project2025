from aiogram import Router, F
from aiogram.filters import Text
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup

from src.backend import misc

# from database.db_commands.user_cmd import get_new_user, activate_user, count_check_users, del_user as del_, \
#     update_group
from src.backend.database.db_cmd.user_cmd import (
    get_new_user,
    activate_user,
    count_check_users,
    del_user as del_,
    update_group,
)
from src.backend.telegram.keyboards.inline import get_confirm_user_kb
from src.backend.telegram.keyboards.reply import get_group_list
from src.backend.telegram.states import admin
from src.backend.text_templates import admin_confirm, admin_cancel

router = Router()


@router.callback_query(Text("show_new_user"))
async def new_user(callback: CallbackQuery):
    if await count_check_users() != 0:
        user = await get_new_user()
        kb = get_confirm_user_kb(user.tg_id)
        await callback.message.answer(f"<pre>{user}</pre>", reply_markup=kb)
    else:
        await callback.message.answer("Новые пользователи закончились")


@router.callback_query(Text(startswith="activate_"))
async def activate(callback: CallbackQuery, state: FSMContext):
    id = int(callback.data.split("_")[1])
    await activate_user(id)
    await state.set_state(admin.GetGroup.get_group)
    await state.update_data(user_id=id)
    await callback.message.answer(
        "Напишите группу для данного пользователя или выберите из предложенных", reply_markup=await get_group_list()
    )


@router.message(F.text, admin.GetGroup.get_group)
async def add_group(message: Message, state: FSMContext):
    data = await state.get_data()
    await update_group(data["user_id"], message.text)
    await state.clear()
    await message.answer(
        f"Пользователю успешно присвоена группа: {message.text}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Показать следующего", callback_data="show_new_user")]]
        ),
    )
    await misc.bot.send_message(data["user_id"], admin_confirm.format(group=message.text))


@router.callback_query(Text(startswith="del_"))
async def get_description(callback: CallbackQuery, state: FSMContext):
    id = int(callback.data.split("_")[1])
    await state.set_state(admin.GetDescription.get_description)
    await state.update_data(user_id=id)
    await callback.message.answer("Почему вы решили отказать?")


@router.message(F.text, admin.GetDescription.get_description)
async def del_user(message: Message, state: FSMContext):
    description = message.text
    data = await state.get_data()
    await del_(data["user_id"])
    text = admin_cancel.format(description=description)
    await misc.bot.send_message(data["user_id"], text)
    await state.clear()
    await message.answer(
        "Мы ему сообщим его ошибку",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Показать следующего", callback_data="show_new_user")]]
        ),
    )
