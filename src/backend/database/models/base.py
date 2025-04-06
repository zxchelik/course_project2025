from datetime import datetime
from typing import Optional, Annotated

from sqlalchemy import BigInteger
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import String

# Custom types
MyShortSTR = Annotated[str, mapped_column(String(63))]
MyLongSTR = Annotated[str, mapped_column(String(255))]
TgId = Annotated[int, mapped_column(BigInteger)]


# Base
class Base(AsyncAttrs, DeclarativeBase):
    created: Mapped[Optional[datetime]] = mapped_column(default=datetime.now)
    updated: Mapped[Optional[datetime]] = mapped_column(default=datetime.now, onupdate=datetime.now)
