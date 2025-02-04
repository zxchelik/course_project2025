from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, MyShortSTR, MyLongSTR, TgId


class CassetteType:
    CASSETTE = "Кассета"
    REMOVABLE = "Съёмное дополнение"
    WELDED = "Приварное дополнение"

    @classmethod
    def to_list(cls) -> list[str]:
        return [cls.CASSETTE, cls.REMOVABLE, cls.WELDED]


class BlankCassettes(Base):
    __tablename__ = "blank_cassettes"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    cassette_name: Mapped[MyShortSTR]
    quantity: Mapped[int]
    is_completed: Mapped[bool] = mapped_column(default=False)
    type: Mapped[MyShortSTR]
    priority: Mapped[int]
    customer_id: Mapped[TgId]
    worker_id: Mapped[TgId | None]

    technical_comment: Mapped[MyLongSTR]
    comment: Mapped[MyLongSTR | None]
