from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ContainerModel(BaseModel):
    number: str
    date_cont: date
    name: str
    color: int
    weight: float
    batch_number: int
    cover_article: str
    comments: Optional[str]
    storage: str

    class Config:
        orm_mode = True


class NamesNode(BaseModel):
    text: str
    value: str
    children: list["NamesNode"] | None = Field(None)


class PlasticModel(BaseModel):
    color: int
    total_weight: float
