from datetime import date

from pydantic import BaseModel, validator

from src.backend.database.models.blank_cassettes import CassetteType
from src.backend.database.models.cassette import CassetteState
from src.backend.database.modelsDTO.container import ContainerModel
from src.backend.database.modelsDTO.user import UserIdFioModel


class StorageMisc(BaseModel):
    storage: str


class RawCassetteModel(BaseModel):
    name: str
    state: str
    type: str
    priority: int

    technical_comment: str
    comment: str | None

    @validator("state")
    def validate_state(cls, value):
        states = CassetteState.to_list()
        if value in states:
            return value
        raise ValueError(f"Invalid state: {value}, but it should be in {states}")

    @validator("type")
    def validate_type(cls, value):
        types = CassetteType.to_list()
        if value in types:
            return value
        raise ValueError(f"Invalid state: {value}, but it should be in {types}")

    def to_str_table_view(self):
        info = [
            ("Наимен.", self.name),
            ("Номер", getattr(self, "number", None)),
            ("Приор.", self.priority),
            ("Тип", self.type),
            ("Склад", getattr(self, "storage", None)),
        ]

        many_lines_info = [
            ("Краны", [i for i in getattr(self, "crane", [])]),
            ("Допы(п)", [i.name for i in getattr(self, "additions", []) if i.type == CassetteType.WELDED]),
            (
                "Допы(с)",
                [f"{i.name} {i.number}" for i in getattr(self, "additions", []) if i.type == CassetteType.REMOVABLE],
            ),
            ("Р. узел", [i.name for i in getattr(self, "additions", []) if i.type == CassetteType.DISSOLVER_UNIT]),
            ("Бочки", [f"{i.name} {i.number}" for i in getattr(self, "containers", [])]),
        ]

        output = ""
        pattern = "{key:<7}:{value:<17}\n"
        pattern_for_many = lambda value: " " * 8 + str(value) + "\n"
        for key, value in info:
            if value:
                output += pattern.format(key=key, value=value)

        for key, values in many_lines_info:
            if values:
                output += pattern.format(key=key, value=values[0] or "")
                for value in values[1:]:
                    output += pattern_for_many(value=value)

        key, value = "Т. ком.", self.technical_comment
        output += pattern.format(key=key, value=value)
        if self.comment:
            key, value = "Ком.", self.comment
            output += pattern.format(key=key, value=value)
        return output

    class Config:
        orm_mode = True


class CassetteModel(RawCassetteModel):
    id: int
    number: str | None

    cut_date: date
    weld_date: date | None
    paint_date: date | None
    assemble_date: date | None
    crane: list[str]

    cutter_id: int | None

    storage: str


class AdditionalModel(CassetteModel):
    cassette_id: int | None


class CassetteModelWithAdditions(CassetteModel):
    additions: list["AdditionalModel"] | None


class CassetteModelWithAdditionsContainers(CassetteModelWithAdditions):
    containers: list["ContainerModel"] | None


class CassetteAssembleModel(CassetteModelWithAdditionsContainers): ...


class CassetteShippingModel(CassetteModelWithAdditionsContainers, StorageMisc): ...


class CassetteNQHModel(BaseModel):
    name: str
    quantity: int
    hash: str


class CassetteNumberModel(BaseModel):
    year_char: str
    group: int
    month: int
    number: int

    def update_group(self, value: int):
        self.group += value

    def update_number(self, value: int):
        self.number += value

    def set_number(self, value: int):
        self.number = value

    def __str__(self):
        return f"{self.year_char}{self.group}.{self.month}.{self.number:0>2}"

    @classmethod
    def from_str(cls, s: str):
        import re

        match = re.fullmatch(r"([А-Яа-яЁё])(\d+)\.(\d+)\.(\d+)", s)
        if not match:
            raise ValueError(f"Invalid format: {s}")
        year_char, group, month, number = match.groups()
        return cls(year_char=year_char, group=int(group), month=int(month), number=int(number))


class WeldCassetteTaskModel(BaseModel):
    task_hash: str
    quantity: int

    raw_cassette: "RawCassetteModel"
    raw_additions: list[str]
    weld_date: date
    numbers: list["CassetteNumberModel"]
    group: list["UserIdFioModel"]
    help_group: list["UserIdFioModel"]

    def to_str_table_view(self):
        info = [("Наимен.", self.raw_cassette.name), ("Тип", self.raw_cassette.type), ("Дата", self.weld_date)]
        many_lines_info = []

        if len(self.numbers) == 1:
            info.append(("Номер", self.numbers[0]))
        elif len(self.numbers) > 1:
            many_lines_info.append(("Номера", [str(i) for i in self.numbers]))

        many_lines_info += [
            ("Допы", self.raw_additions),
            ("Группа", [i.fio for i in self.group] + [i.fio + "(П)" for i in self.help_group]),
        ]

        output = ""
        pattern = "{key:<7}:{value:<17}\n"
        pattern_for_many = lambda value: " " * 8 + str(value) + "\n"
        for key, value in info:
            if value:
                output += pattern.format(key=key, value=str(value))

        for key, values in many_lines_info:
            if values:
                output += pattern.format(key=key, value=values[0] or "")
                for value in values[1:]:
                    output += pattern_for_many(value=value)

        key, value = "Т. ком.", self.raw_cassette.technical_comment
        output += pattern.format(key=key, value=value)
        if self.raw_cassette.comment:
            key, value = "Ком.", self.raw_cassette.comment
            output += pattern.format(key=key, value=value)
        return output
