from typing import List, TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.database.models import Base

if TYPE_CHECKING:
    from src.backend.database.models import User


class Role(Base):
    __tablename__ = "role"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]  # например, "аналитик", "менеджер", "администратор"

    users: Mapped[List["User"]] = relationship(secondary="user_role", back_populates="roles")


class UserRole(Base):
    __tablename__ = "user_role"
    user_id: Mapped[int] = mapped_column(ForeignKey("user_data.tg_id"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"), primary_key=True)
