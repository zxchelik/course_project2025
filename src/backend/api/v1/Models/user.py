from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, Extra

from src.backend.api.v1.Models.role import RoleRead


class UserBase(BaseModel):
    fio: str
    group: Optional[str] = Field(None)
    birthday: date
    status: Optional[str] = Field("check")
    is_admin: bool = False
    user_login: Optional[str] = Field(None)


class UserCreate(UserBase):
    tg_id: int
    hashed_password: Optional[str] = Field(None)

    class Config:
        extra = Extra.ignore


class UserUpdate(BaseModel):
    fio: Optional[str] = Field(None)
    group: Optional[str] = Field(None)
    birthday: Optional[date] = Field(None)
    status: Optional[str] = Field(None)
    is_admin: Optional[bool] = Field(None)
    user_login: Optional[str] = Field(None)
    hashed_password: Optional[str] = Field(None)

    class Config:
        extra = Extra.ignore


class UserRead(UserBase):
    tg_id: int
    created: Optional[date] = Field(None)
    updated: Optional[date] = Field(None)

    class Config:
        orm_mode = True


class UserRolesResponse(BaseModel):
    roles: list[RoleRead]

    class Config:
        orm_mode = True
