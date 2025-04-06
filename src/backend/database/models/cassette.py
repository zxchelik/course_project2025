from datetime import date
from typing import TYPE_CHECKING, List

import sqlalchemy.sql
from sqlalchemy import String, ForeignKey, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, MyShortSTR, MyLongSTR, TgId

if TYPE_CHECKING:
    from src.backend.database.models.user import User
    from src.backend.database.models import Container
    from src.backend.database.models.cassette_group_member import CassetteGroupMember
    from src.backend.database.models.assembly_step import AssemblyStep


class CassetteState:
    CUT = "Нарезанная"
    WELD = "Сваренная"
    PAINT = "Покрашенная"
    ASSEMBLE = "Собранная"
    SHIP = "Отгруженная"

    @classmethod
    def to_list(cls):
        return [cls.CUT, cls.WELD, cls.PAINT, cls.ASSEMBLE, cls.SHIP]


class Cassette(Base):
    __tablename__ = "cassette"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    number: Mapped[str | None] = mapped_column(String(63), unique=True)
    name: Mapped[MyShortSTR]
    priority: Mapped[int] = mapped_column(server_default="0")
    state: Mapped[MyShortSTR] = mapped_column(server_default=CassetteState.CUT)  # CassetteState
    type: Mapped[str]  # CassetteType
    cassette_id: Mapped[int | None] = mapped_column(
        ForeignKey("cassette.id", ondelete="SET NULL", onupdate="CASCADE")
    )  # Only for additions
    in_working: Mapped[bool] = mapped_column(server_default=sqlalchemy.sql.false())
    crane: Mapped[List[str]] = mapped_column(
        MutableList.as_mutable(ARRAY(String)), nullable=False, server_default=text("ARRAY[]::VARCHAR[]")
    )

    cut_date: Mapped[date]
    weld_date: Mapped[date | None]
    paint_date: Mapped[date | None]

    cutter_id: Mapped[TgId | None] = mapped_column(
        ForeignKey(column="user_data.tg_id", ondelete="SET NULL", onupdate="CASCADE")
    )
    technical_comment: Mapped[MyLongSTR]
    comment: Mapped[MyLongSTR | None]
    storage: Mapped[str] = mapped_column(String(63), server_default="Н/Д")

    cutter: Mapped["User"] = relationship()
    groups: Mapped[List["CassetteGroupMember"] | None] = relationship()
    additions: Mapped[List["Cassette"] | None] = relationship()
    assembly_steps: Mapped[List["AssemblyStep"]] = relationship()
    containers: Mapped[List["Container"]] = relationship(back_populates="cassette")
