from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from database.models.user import USER
    from database.models.container import Container


class Groups(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    container: Mapped["Container"] = relationship(back_populates="group", uselist=False, lazy=False)
    users: Mapped[list["USER"]] = relationship(
        back_populates="groups", uselist=True, secondary="group_membership", lazy=False
    )

    def __repr__(self):
        return f"<{self.id=}>"


class GroupsMembership(Base):
    __tablename__ = "group_membership"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user_data.tg_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True
    )
