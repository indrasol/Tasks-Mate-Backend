from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class ProjectTeamAdd(BaseModel):
    user_id: UUID
    role: str


class ProjectTeamUpdateRole(BaseModel):
    role: str


class ProjectTeamMemberOut(BaseModel):
    id: UUID
    name: Optional[str]
    email: str
    role: str

    class Config:
        orm_mode = True
