from aiogram import Router
from aiogram.filters import Text
from aiogram.types import CallbackQuery

from keyboards.inline import get_inline_kb

router = Router()


@router.callback_query(Text('cassette_menu'))
async def start(callback: CallbackQuery):
    kb = get_inline_kb([
        [("Нарезать детали", "start_cassette_cutting"), ("Сварить изделие", "weld_cassette")],
        [("Покрасить изделие", "paint_cassette")]
    ])
    text = "Выберите действие"
    await callback.message.edit_text(text=text, reply_markup=kb)
