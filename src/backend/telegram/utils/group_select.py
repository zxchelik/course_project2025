from typing import Callable, Awaitable, TypeAlias, overload, Optional, Any

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pydantic import BaseModel, Field

from src.backend.database.db_cmd.user_cmd import get_user, get_all_users_for_group_select
from src.backend.database.modelsDTO.user import UserIdFioModel

GetUsersFuncType: TypeAlias = Callable[[], Awaitable[list[UserIdFioModel]]]


class GroupSelectorCallbackData(CallbackData, prefix="GroupSelector"):
    """
    :param action:  ch_page     |select |confirm    |ignore
    :param value:   int         |int    |bool/None  |None
    """

    action: str
    value: int | bool | None = None


class UserGroup(BaseModel):
    group: list[UserIdFioModel]
    help_group: list[UserIdFioModel] | None


class GroupSelector:
    """
    Usage example:
    async def start_select_group(callback: CallbackQuery, state: FSMContext):
        await state.set_state(STATEGROUP.select_group)
        group_selector = GroupSelector(user_id=callback.from_user.id)
        await group_selector.start(callback=callback)
        await state.update_data(group_selector=group_selector)

    @router.callback_query(StateFilter(STATEGROUP.select_group),GroupSelectorCallbackData.filter())
    async def process_select_group(callback: CallbackQuery, callback_data: GroupSelectorCallbackData, state: FSMContext):
        data = await state.get_data()
        group_selector: GroupSelector = data.get("group_selector")
        if await group_selector.process(callback, callback_data):
            group_users, help_group_users = group_selector.get_result()
            await state.update_data(
                group_users=group_users,
                help_group_users=help_group_users
            )
            await START_NEXT_STEP(callback, state)
        await state.update_data(group_selector=group_selector)

    """

    get_user_list: GetUsersFuncType
    all_users: list[UserIdFioModel] | None
    user_id: int
    is_help_enabled: bool
    page_size: int
    current_page: int
    user: UserIdFioModel | None = None
    _users: dict[int, UserIdFioModel]
    _help_users: dict[int, UserIdFioModel]

    def __init__(
        self,
        user_id: int,
        get_user_list: GetUsersFuncType = get_all_users_for_group_select,
        is_help_enabled: bool = True,
        page_size: int = 5,
    ) -> None:
        """
        :param get_user_list: () -> list[UserIdFioModel]
        :param user_id: user_id that should be ignored
        :param is_help_enabled: True if help_users are used
        :param page_size: number of users per message
        """
        self.get_user_list = get_user_list
        self.user_id = user_id
        self.is_help_enabled = is_help_enabled
        self.page_size = page_size

        self._users = {}
        self._help_users = {}
        self.current_page = 0

    @overload
    async def start(self, callback: CallbackQuery) -> None: ...

    @overload
    async def start(self, message: Message, state: FSMContext, old_msg_name: str) -> None: ...

    async def start(
        self,
        callback: Optional[CallbackQuery] = None,
        message: Optional[Message] = None,
        state: Optional[FSMContext] = None,
        old_msg_name: Optional[str] = None,
    ) -> None:
        self.all_users = await self.get_user_list()
        for i, user in enumerate(self.all_users):
            if user.id == self.user_id:
                self.user = self.all_users.pop(i)
        if not self.user:
            user = await get_user(user_id=self.user_id)
            self.user = UserIdFioModel(id=user.tg_id, fio=user.fio)

        kb = self._get_kb()
        text = self._get_text()
        if callback:
            await callback.message.edit_text(text=text, reply_markup=kb)
        elif message and state:
            mess = message.answer(text=text, reply_markup=kb)
            if old_msg_name:
                data: dict[str, Any] = await state.get_data()
                msg: Message = data.get(old_msg_name)
                await msg.delete()
                await state.update_data({old_msg_name: mess})
            await message.delete()
        else:
            raise ValueError("Invalid arguments provided to start method.")

    async def process(self, callback: CallbackQuery, callback_data: GroupSelectorCallbackData) -> bool:
        """
        Processes the callback based on the action specified in the callback data.

        :return: True if processing is finished
        """
        match callback_data.action:
            case "ch_page":
                await self._process_ch_page(callback, callback_data)
            case "select":
                await self._process_select(callback, callback_data)
            case "confirm":
                return await self._process_confirm(callback, callback_data)
            case "ignore":
                await callback.answer()

        return False

    def get_result(self) -> list[UserIdFioModel] | tuple[list[UserIdFioModel], list[UserIdFioModel]]:
        if self.is_help_enabled:
            return [self.user] + list(self._users.values()), list(self._help_users.values())
        else:
            return [self.user] + list(self._users.values())

    def get_result_dto(self) -> UserGroup:
        if self.is_help_enabled:
            return UserGroup(group=[self.user] + list(self._users.values()), help_group=list(self._help_users.values()))
        return UserGroup(group=[self.user] + list(self._users.values()), help_group=None)

    def add_user(self, value: int):
        user = self.all_users[value]
        if user.id in self._users:
            self._users.pop(user.id)
            if self.is_help_enabled:
                self._help_users[user.id] = user
        elif user.id in self._help_users:
            self._help_users.pop(user.id)
        else:
            self._users[user.id] = user

    async def _process_ch_page(self, callback: CallbackQuery, callback_data: GroupSelectorCallbackData) -> None:
        value = callback_data.value
        if isinstance(value, int):
            self.current_page += value
        else:
            raise ValueError("Invalid value type")
        await self._display(callback)

    async def _process_select(self, callback: CallbackQuery, callback_data: GroupSelectorCallbackData) -> None:
        value = callback_data.value
        if isinstance(value, int):
            self.add_user(value)
        else:
            raise ValueError("Invalid value type")
        await self._display(callback)

    async def _process_confirm(self, callback: CallbackQuery, callback_data: GroupSelectorCallbackData) -> bool:
        value = callback_data.value
        if value is None:  # unused
            text = self._get_text()
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Подтвердить✅",
                            callback_data=GroupSelectorCallbackData(action="confirm", value=True).pack(),
                        ),
                        InlineKeyboardButton(
                            text="Отменить❌",
                            callback_data=GroupSelectorCallbackData(action="confirm", value=False).pack(),
                        ),
                    ]
                ]
            )
            await callback.message.edit_text(text=text, reply_markup=kb)
            return False
        elif isinstance(value, (bool, int)):
            if value:
                return True
            else:
                await self._display(callback)
        else:
            raise ValueError("Invalid value type")

    async def _display(self, callback: CallbackQuery):
        kb = self._get_kb()
        text = self._get_text()
        await callback.message.edit_text(text=text, reply_markup=kb)

    def _get_text(self) -> str:
        sep = "\n"
        res = f"Состав бригады\nТы выбрал:\n\n{self.user.fio}"
        res += sep + sep.join([i.fio for i in self._users.values()])
        if self._help_users:
            res += "\n" + ("(П)" + sep).join([i.fio for i in self._help_users.values()]) + "(П)"
        return res

    def _get_kb(self) -> InlineKeyboardMarkup:
        """
        :return: InlineKB with users
        """

        max_page = len(self.all_users) // self.page_size + (len(self.all_users) % self.page_size != 0) - 1
        users = self.all_users[self.current_page * self.page_size : (self.current_page + 1) * self.page_size]

        builder = InlineKeyboardBuilder()

        for i, user in enumerate(users):
            builder.button(
                text=user.fio,
                callback_data=GroupSelectorCallbackData(
                    action="select",
                    value=self.page_size * self.current_page + i,  # Вычисляем номер в массиве всех пользователей
                ),
            )

        counter = 0
        if self.current_page > 0:
            builder.button(text="⬅️", callback_data=GroupSelectorCallbackData(action="ch_page", value=-1))
            counter += 1
        if self.current_page < max_page:
            builder.button(text="➡️", callback_data=GroupSelectorCallbackData(action="ch_page", value=1))
            counter += 1

        builder.button(text="✅Закончить", callback_data=GroupSelectorCallbackData(action="confirm", value=True))

        if counter != 0:
            builder.adjust(*[1 for _ in users], counter, 1)
        else:
            builder.adjust(*[1 for _ in users], 1)
        return builder.as_markup()
