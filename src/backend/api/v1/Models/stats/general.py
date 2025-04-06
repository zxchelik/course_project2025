from datetime import date

from pydantic import BaseModel


class ProducedCount(BaseModel):
    produced_date: date
    count: int
