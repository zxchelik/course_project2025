from typing import Optional

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Names(Base):
    __tablename__ = "names"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(String(63))
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("names.id"))
    price: Mapped[float | None]
    points: Mapped[float | None]

    def __str__(self):
        return f"{self.name} цена:{self.price or 0} очки:{self.points or 0}"
