from sqlalchemy import String, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class StorageMovements(Base):
    __tablename__ = "storage_movements"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    product_number: Mapped[str] = mapped_column(String(63))
    from_storage: Mapped[str] = mapped_column(String(63))
    to_storage: Mapped[str] = mapped_column(String(63))
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user_data.tg_id"), onupdate="CASCADE", server_default="106789396"
    )
    reasons_for_moving: Mapped[str | None] = mapped_column(String(63))

    def __str__(self):
        return f"{self.product_number}: {self.from_storage}  -> {self.to_storage}|{self.created}"
