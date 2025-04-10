from datetime import date
from typing import Optional, TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, MyShortSTR, MyLongSTR

if TYPE_CHECKING:
    from .role import Role
    from src.backend.database.models.groups import Groups


class User(Base):
    __tablename__ = "user_data"

    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    fio: Mapped[str] = mapped_column(String(63))
    group: Mapped[Optional[str]] = mapped_column(String(63))
    birthday: Mapped[date]
    status: Mapped[Optional[str]] = mapped_column(String(63), default="check")
    is_admin: Mapped[bool] = mapped_column(default=False)
    user_login: Mapped[MyShortSTR | None]
    hashed_password: Mapped[MyLongSTR | None]

    groups: Mapped[list["Groups"]] = relationship(back_populates="users", uselist=True, secondary="group_membership")
    roles: Mapped[list["Role"]] = relationship("Role", secondary="user_role", back_populates="users")

    def __repr__(self):
        return f"""{self.fio} - {self.group} - {self.tg_id}
{'Дата рождения': <15}|{self.birthday}
{'Статус': <15}|{self.status}
{'Админ': <15}|{self.is_admin}
{"Зарегистрирован":15}|{self.created.strftime('%y.%m.%d %H:%M')}
{"Изменён":15}|{self.updated.strftime('%y.%m.%d %H:%M')}"""
