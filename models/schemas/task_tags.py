from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class TagCreate(BaseModel):
    name: str
    color: Optional[str]


class TagUpdate(BaseModel):
    name: Optional[str]
    color: Optional[str]


class TagOut(BaseModel):
    id: UUID
    name: str
    color: Optional[str]

    class Config:
        orm_mode = True
