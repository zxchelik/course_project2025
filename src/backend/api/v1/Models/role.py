from typing import Optional

from pydantic import BaseModel


class RoleBase(BaseModel):
    name: str


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = None


class RoleRead(RoleBase):
    id: int

    class Config:
        orm_mode = True


class RoleAssign(BaseModel):
    user_id: int
