from datetime import date
from typing import Optional, TYPE_CHECKING

from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from database.models.user import USER


class HourlyWork(Base):
    __tablename__ = 'hourly_work'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_data.tg_id"), onupdate="CASCADE")
    name: Mapped[str] = mapped_column(String(63))
    duration: Mapped[float]
    comment: Mapped[Optional[str]] = mapped_column(String(255))
    date_: Mapped[date]

    user: Mapped["USER"] = relationship(lazy=False)

    def get_info_for_exel(self) -> (int, list):
        return self.user.fio, [self.date_.strftime("%d.%m.%y"), None, self.name, self.duration, None,
                               self.comment or ""]
