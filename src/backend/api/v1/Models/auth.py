from pydantic import BaseModel

from src.backend.api.v1.Models.user import UserRead


class TokenSchema(BaseModel):
    access_token: str
    token_type: str
    user: UserRead


class RegistrationSchema(BaseModel):
    tg_id: int
    user_login: str
    password: str
