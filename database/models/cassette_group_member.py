from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, MyShortSTR

if TYPE_CHECKING:
    from database.models.user import USER


class CassetteGroupMemberType:
    WELDER = "Св"
    WELDER_HELPER = "СвП"
    PAINTER = "М"
    PAINTER_HELPER = "МП"
    ASSEMBLER = "Сб"
    ASSEMBLER_HELPER = "СбП"


class CassetteGroupMember(Base):
    __tablename__ = "cassette_group_member"

    cassette_id: Mapped[int] = mapped_column(
        ForeignKey("cassette.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True
    )
    tg_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user_data.tg_id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True
    )
    percent: Mapped[float]
    group_type: Mapped[MyShortSTR]  # CassetteGroupMemberType

    user: Mapped["USER"] = relationship(lazy="selectin")
