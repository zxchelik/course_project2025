from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PlasticSupply(Base):
    __tablename__ = "plastic_supply"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    color_number: Mapped[int]
    weight: Mapped[float]
