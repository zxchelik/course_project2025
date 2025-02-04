from aiogram import Router
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from database.db_cmd.names_cmd import add_name
from filters.db_filters import CheckStatus
from handlers.user.message.different import send_menu
from keyboards.name_ikb import edit_name_fub, SelectName
from keyboards.reply import get_reply_keyboard
from states.admin import AddName
from text_templates import text010, text020

router = Router()


@router.callback_query(CheckStatus('active'), Text('add_name'))
async def start_add_name(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddName.select_page)
    text = text010
    await callback.message.edit_text(text=text, reply_markup=await edit_name_fub())


@router.callback_query(SelectName.filter(), StateFilter(AddName.select_page))
async def select_page(callback: CallbackQuery, callback_data: SelectName):
    page = callback_data.page
    parent_id = callback_data.parent_id
    await callback.message.edit_reply_markup(reply_markup=await edit_name_fub(parent_id, page=page))


@router.callback_query(StateFilter(AddName.select_page), Text(startswith="add_"))
async def start_add_name(callback: CallbackQuery, state: FSMContext):
    await state.update_data(parent_id=callback.data.split('_')[1])
    await state.set_state(AddName.add_name)
    text = text020
    await callback.message.delete()
    mes = await callback.message.answer(text=text, reply_markup=get_reply_keyboard('❌Назад'))
    await state.update_data(mes=mes)


@router.message(StateFilter(AddName.add_name))
async def add_name_handler(message: Message, state: FSMContext):
    await message.delete()
    msg: Message = (await state.get_data()).get("mes")
    await msg.delete()
    new_name = message.text
    data = await state.get_data()
    parent_id = data.get("parent_id")
    try:
        parent_id = int(parent_id)
    except ValueError:
        parent_id = None
    await state.set_state(AddName.select_page)

    if new_name == "❌Назад":
        return await message.answer(text=text010,
                                    reply_markup=await edit_name_fub(parent_id=parent_id))

    try:
        await add_name(name=new_name, parent_id=parent_id)
        text = f"✅Наименование успешно добавлено"
    except Exception as error:
        text = "❌ПРОИЗОШЛА ОШИБКА"
        logger.error(error)

    await message.answer(text=text, reply_markup=await edit_name_fub(parent_id=parent_id))


@router.callback_query(StateFilter(AddName), Text('finish'))
async def finish_edit_name(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await send_menu(callback.message, edit=True, is_admin=True)
