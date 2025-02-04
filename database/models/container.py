from datetime import date
from typing import Optional, TYPE_CHECKING, List

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from . import ContGroupMember
    from database.models.groups import Groups


class Container(Base):
    """Таблица описывающая бочки"""
    __tablename__ = "container"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    number: Mapped[str] = mapped_column(String(63), unique=True)
    date_cont: Mapped[date]
    name: Mapped[str] = mapped_column(String(63))
    color: Mapped[int]
    weight: Mapped[float]
    batch_number: Mapped[int]
    cover_article: Mapped[str]
    comments: Mapped[Optional[str]] = mapped_column(String(255))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    percent: Mapped[float]
    storage: Mapped[str] = mapped_column(String(63), server_default="Н/Д")

    group: Mapped["Groups"] = relationship(back_populates="container")
    group_members: Mapped[List["ContGroupMember"]] = relationship(lazy='selectin', back_populates="container")

    def __str__(self) -> str:
        args = [
            ('Дата', self.date_cont),
            ('№ бочки', self.number),
            ('Наимен.', self.name),
            ('Цвет', self.color),
            ('Масса пл.', self.weight),
            ('Партия пл.', self.batch_number),
            ('Арт. крыш.', self.cover_article),
            ('№ Бригады', self.group_id)
        ]

        res = f"{'-' * 10}+{'-' * 16}"
        for data, value in args:
            res += f"""\n{data: <10}+{value: <14}
{'-' * 10}+{'-' * 16}"""
        res += f'\nКоммент.: {self.comments}'
        return res

    def __repr__(self) -> str:
        return f"<Container number={self.number}>"

    def get_data_list(self) -> list:
        return [self.number,
                self.date_cont.strftime("%d.%m.%Y"),
                self.name,
                self.color,
                self.weight,
                self.batch_number,
                self.cover_article,
                ", ".join([i.fio for i in self.group.users]),
                None,
                self.comments]

    def get_info_for_exel(self):
        return self.group.users, [self.date_cont.strftime("%d.%m.%y"), self.name, self.number, self.percent * 2]
