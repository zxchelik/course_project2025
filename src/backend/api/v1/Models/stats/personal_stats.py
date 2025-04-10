from pydantic import BaseModel


class PersonalStat(BaseModel):
    title: str
    info: str
