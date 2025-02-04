from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, List, Annotated

import sqlalchemy.sql
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, MyShortSTR, MyLongSTR, TgId

if TYPE_CHECKING:
    from database.models.user import USER
    from database.models.cassette_group_member import CassetteGroupMember


class CassetteState:
    CUTED = "Нарезанная"
    WELDED = "Сваренная"
    PAINTED = "Покрашенная"
    ASSEMBLED = "Собранная"
    SHIPED = "Отгруженная"

    @classmethod
    def to_list(cls):
        return [cls.CUTED, cls.WELDED, cls.PAINTED, cls.ASSEMBLED, cls.SHIPED]


class Cassette(Base):
    __tablename__ = "cassette"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    number: Mapped[str | None] = mapped_column(String(63), unique=True)
    name: Mapped[MyShortSTR]
    priority: Mapped[int] = mapped_column(server_default="0")
    state: Mapped[MyShortSTR] = mapped_column(server_default=CassetteState.CUTED)  # CassetteState
    type: Mapped[str]
    cassette_id: Mapped[int | None] = mapped_column(
        ForeignKey("cassette.id", ondelete="SET NULL", onupdate="CASCADE")
    )  # Only for additions
    in_working: Mapped[bool] = mapped_column(server_default=sqlalchemy.sql.false())

    cut_date: Mapped[date]
    weld_date: Mapped[date | None]
    paint_date: Mapped[date | None]
    assemble_date: Mapped[date | None]

    cutter_id: Mapped[TgId | None] = mapped_column(
        ForeignKey(column="user_data.tg_id", ondelete="SET NULL", onupdate="CASCADE")
    )

    technical_comment: Mapped[MyLongSTR]
    comment: Mapped[MyLongSTR | None]

    storage: Mapped[str] = mapped_column(String(63), server_default="Н/Д")

    cutter: Mapped["USER"] = relationship()
    groups: Mapped[List["CassetteGroupMember"] | None] = relationship()

    additions: Mapped[List["Cassette"] | None] = relationship()
