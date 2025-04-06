from datetime import date

from pydantic import BaseModel

from src.backend.database.modelsDTO.cassette import CassetteModelWithAdditions
from src.backend.telegram.keyboards.cassete.painting import PaintType


class PaintingTask(BaseModel):
    user_id: int
    cassette: CassetteModelWithAdditions | None
    painting_date: date | None
    types: list[PaintType] | None
    is_finished: bool | None

    def get_types_result(self):
        return [f"М({i.value})" for i in self.types]

    def __str__(self):
        sep = ",\n       "
        return f"""<pre>номер :{self.cassette.number}
наимен:{self.cassette.name}
дата  :{self.painting_date}
допы  :{sep.join([i.name for i in self.cassette.additions])}
типы  :{', '.join([i.text for i in self.types])}</pre>"""
