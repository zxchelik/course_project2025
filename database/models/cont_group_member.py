from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from database.models.user import USER
    from database.models.container import Container


class ContGroupMember(Base):
    __tablename__ = 'cont_group_member'

    container_number: Mapped[str] = mapped_column(String(63), ForeignKey("container.number"), primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_data.tg_id"), primary_key=True)
    user_percent: Mapped[float]

    container: Mapped["Container"] = relationship(back_populates="group_members")
    user: Mapped["USER"] = relationship(lazy="selectin")

    def __repr__(self):
        return f"<{self.container_number=} {self.tg_id=} {self.user_percent=}>"
