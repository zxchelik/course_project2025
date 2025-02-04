from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pydantic import BaseModel


class PaintType(BaseModel):
    value: str
    percent: float
    is_selected: bool = False
    is_locked: bool = False

    def toggle(self):
        self.is_selected = not self.is_selected


class PaintTypeSelectorCallbackData(CallbackData, prefix="PaintTypeSelectorCallbackData"):
    """
    :param action:  select |confirm |select_all
    :param value:   int    |None    |None
    """

    action: str
    value: int | None = None


class PaintTypesSelector:
    _message: Message
    _message_text: str
    _types: list[PaintType]

    def __init__(self, message: Message, types=None, message_text="Выбери сделанные этапы покраски"):
        if types is None:
            types = ["Подготовка", "Грунтовка", "Покраска"]
        self._message = message
        self._types = [PaintType(value=i) for i in types]
        self._message_text = message_text

    async def _display(self): ...

    def build_kb(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for i, t in enumerate(self._types):
            builder.button(text=t.value, callback_data=PaintTypeSelectorCallbackData(action="select", value=i))
