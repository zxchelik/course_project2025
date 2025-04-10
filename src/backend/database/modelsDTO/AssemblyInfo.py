from pydantic import BaseModel, Field

from database.modelsDTO.cassette import CassetteModel
from database.modelsDTO.user import UserIdFioModel


class AssemblyInfo(BaseModel):
    cassette: CassetteModel
