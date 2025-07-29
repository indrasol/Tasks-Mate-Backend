# models/schemas/organization.py

from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class OrganizationBase(BaseModel):
    name: str = Field(..., example="My Organization")
    description: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]


class OrganizationInDB(OrganizationBase):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True


class OrganizationMember(BaseModel):
    id: UUID
    name: str
    email: str
    role: Optional[str]
    status: str


class OrganizationDetails(OrganizationInDB):
    members: List[OrganizationMember] = []
    projects: List[dict] = []
