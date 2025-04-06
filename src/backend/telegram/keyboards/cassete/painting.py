from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pydantic import BaseModel, Field


class PaintType(BaseModel):
    text: str
    value: int
    is_selected: bool = Field(False)
    is_locked: bool

    def toggle(self) -> None:
        self.is_selected = not self.is_selected

    def turn_on(self) -> None:
        self.set_is_selected(True)

    def set_is_selected(self, value: bool):
        if self.is_locked:
            return
        self.is_selected = value


class PaintTypeSelectorCallbackData(CallbackData, prefix="PaintTypeSelectorCallbackData"):
    """
    :param action:  select |confirm |select_all |ignore
    :param value:   int    |None    |None       |None
    """

    action: str
    value: int | None = None


class PaintTypesSelector:
    _message_text: str
    _types: list[PaintType]

    def __init__(self, locked_types: set[int], message_text="Выбери сделанные этапы покраски", types=None):
        if types is None:
            types = [("Подготовка", 1), ("Грунтовка", 2), ("Покраска", 3)]
        self._types = [PaintType(text=text, value=i, is_locked=i in locked_types) for text, i in types]
        self._message_text = message_text

    async def start(self, callback: CallbackQuery):
        await self._display(callback)

    @property
    def is_all_selected(self):
        return all((t.is_selected or t.is_locked for t in self._types))

    async def _display(self, callback: CallbackQuery):
        kb = self._build_kb()
        await callback.message.edit_text(text=self._message_text, reply_markup=kb)

    def _build_kb(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for i, t in enumerate(self._types):
            if t.is_locked:
                builder.button(text="🔒 " + t.text, callback_data=PaintTypeSelectorCallbackData(action="ignore"))
            else:
                builder.button(
                    text="✅ " + t.text if t.is_selected else t.text,
                    callback_data=PaintTypeSelectorCallbackData(action="select", value=i),
                )
        builder.button(text="Выбрать всё", callback_data=PaintTypeSelectorCallbackData(action="select_all"))
        builder.button(text="Закончить", callback_data=PaintTypeSelectorCallbackData(action="confirm"))
        builder.adjust(len(self._types), 1, 1)
        return builder.as_markup()

    async def process(
        self, callback: CallbackQuery, callback_data: PaintTypeSelectorCallbackData
    ) -> tuple[bool, None | list[PaintType], None | bool]:
        match callback_data.action:
            case "ignore":
                await callback.answer()
                return False, None, None
            case "select":
                if not isinstance(callback_data.value, int):
                    raise ValueError()
                self._types[callback_data.value].toggle()
                await self._display(callback)
                return False, None, None
            case "select_all":
                is_all_selected = self.is_all_selected
                [i.set_is_selected(not is_all_selected) for i in self._types if not i.is_locked]
                await self._display(callback)
                return False, None, None
            case "confirm":
                return (
                    True,
                    [i for i in self._types if i.is_selected],
                    self.is_all_selected,
                )
