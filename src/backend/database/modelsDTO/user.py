from datetime import date

from pydantic import BaseModel


class UserModel(BaseModel):
    tg_id: int
    fio: str
    group: str | None
    birthday: date
    status: str
    is_admin: bool


class UserIdFioModel(BaseModel):
    id: int
    fio: str
