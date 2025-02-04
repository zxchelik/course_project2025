import os

import pandas
from aiogram import Router, F, Bot
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from database.db_cmd.names_cmd import select_product, get_parent, update
from filters.db_filters import IsAdmin
from handlers.user.message.different import send_menu
from keyboards.inline import get_inline_kb
from states.admin import UpdateNames

router = Router()


@router.callback_query(Text('edit_name_price'), IsAdmin())
async def edit_name_price(callback: CallbackQuery, state: FSMContext):
    kb = get_inline_kb([
        [("Получить шаблон", "get_pattern")]
    ])
    await state.set_state(UpdateNames.update_names)
    text = "Пришли файл"
    await callback.message.edit_text(text, reply_markup=kb)


@router.message(F.document, StateFilter(UpdateNames.update_names))
async def get_document(message: Message, bot: Bot):
    document = message.document

    if not document.file_name.endswith(".xlsx"):
        await message.answer("Данное расширение файла не поддерживается. Пришли .xlsx файл")
        return

    mess = await message.answer("Считываю данные...")

    await bot.download(document, "tmp.xlsx")  # FIXME избавиться от "буферного" файла
    p = pandas.read_excel("tmp.xlsx", engine="openpyxl", sheet_name="Прайс")
    frame = pandas.DataFrame(p)

    for _, row in frame.iterrows():
        id = row.get("id")
        points = row.get("Очки")
        price = row.get("Цена")
        await update(id=id, points=points, price=price)

    await mess.edit_text("✅Данные успешно обновлены✅")


@router.callback_query(Text("get_pattern"), StateFilter(UpdateNames.update_names))
async def get_pattern(callback: CallbackQuery, bot: Bot):
    await callback.message.edit_text("Генерирую файл...")
    wb = Workbook()
    del wb["Sheet"]
    ws: Worksheet = wb.create_sheet("Прайс")
    ws.append(["id", "Очки", "Цена", "Наименование", "Наименование родителя"])

    products = await select_product()

    for product in products:
        parent = await get_parent(id=product.parent_id)
        ws.append([product.id, product.points or 0, product.price or 0, product.name, parent.name,
                   f"{parent.name}-{product.name}"])

    wb.save("names.xlsx")

    await callback.message.delete()
    await bot.send_document(
        callback.message.chat.id,
        FSInputFile("names.xlsx"),
        caption="Пришли изменённый файл"
    )
    os.remove("names.xlsx")


@router.callback_query(Text("user_menu"), IsAdmin())
async def process_user_menu(callback: CallbackQuery):
    await send_menu(callback.message, is_admin=False, edit=True)
