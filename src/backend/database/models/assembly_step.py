from datetime import date
from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.database.models.base import Base, MyShortSTR

if TYPE_CHECKING:
    from src.backend.database.models import Cassette, User


class AssemblyStepTypes:
    ADDITION = "Дополнение"
    CONTAINER = "Бочка"
    CRANE = "Кран"
    DISSOLVER_UNIT = "Растворный узел"


class AssemblyStep(Base):
    __tablename__ = "assembly_step"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cassette_id: Mapped[int] = mapped_column(ForeignKey("cassette.id", ondelete="CASCADE", onupdate="CASCADE"))

    assemble_type: Mapped[MyShortSTR]
    assemble_date: Mapped[date]
    component_id: Mapped[int | None]

    cassette: Mapped["Cassette"] = relationship(back_populates="assembly_steps")
    users: Mapped[List["User"]] = relationship(secondary="assembly_step_user", lazy="selectin")


class AssemblyStepUser(Base):
    __tablename__ = "assembly_step_user"

    assembly_step_id: Mapped[int] = mapped_column(
        ForeignKey("assembly_step.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_data.tg_id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True
    )
