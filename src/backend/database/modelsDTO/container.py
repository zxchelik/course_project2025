from datetime import date
from typing import Optional

from pydantic.main import BaseModel


class ContainerModel(BaseModel):
    id: int
    number: str
    date_cont: date
    name: str
    color: int
    weight: float
    batch_number: int
    cover_article: str
    comments: Optional[str]
    percent: float
    storage: str
    cassette_id: int | None

    class Config:
        orm_mode = True

    def to_str_table_view(self):
        args = [
            ("Дата", self.date_cont),
            ("№ бочки", self.number),
            ("Наимен.", self.name),
            ("Цвет", self.color),
            ("Масса пл.", self.weight),
            ("Партия пл.", self.batch_number),
            ("Арт. крыш.", self.cover_article),
        ]

        res = f"{'-' * 10}+{'-' * 16}"
        for data, value in args:
            res += f"\n{data: <10}|{str(value)}"
            res += f"\n{'-' * 10}+{'-' * 16}"
        res += f"\nКоммент.: {self.comments}"
        return res
