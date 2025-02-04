from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import keyboards.inline
from filters.db_filters import CheckStatus, IsAdmin
from text_templates import menu, help as help_mes

router = Router()


@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(help_mes)

@router.message(Command('id'))
async def get_chat_id(message:Message):
    await message.answer(message.chat.id)


async def send_menu(message: Message, is_admin: bool = False, edit: bool = False):
    menu_text = menu
    kb = keyboards.inline.menu_kb(is_admin=is_admin)
    if edit:
        await message.edit_text(text=menu_text, reply_markup=kb, parse_mode='HTML')
    else:
        await message.answer(text=menu_text, reply_markup=kb, parse_mode='HTML')


@router.message(Command('menu'), CheckStatus('active'), IsAdmin())
async def admin_menu_message(message: Message, state: FSMContext):
    await state.clear()
    await send_menu(message=message, is_admin=True)


@router.message(Command('menu'), CheckStatus('active'))
async def menu_message(message: Message, state: FSMContext):
    await state.clear()
    await send_menu(message=message)
