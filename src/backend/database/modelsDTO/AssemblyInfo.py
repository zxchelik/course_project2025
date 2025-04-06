from pydantic import BaseModel, Field

from src.backend.database.modelsDTO.cassette import CassetteModel
from src.backend.database.modelsDTO.user import UserIdFioModel


class AssemblyInfo(BaseModel):
    cassette: CassetteModel
