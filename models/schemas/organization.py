from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class OrganizationBase(BaseModel):
    name: str
    description: Optional[str]
    logo: Optional[str]
    email: Optional[str]
    metadata: Optional[dict]

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(OrganizationBase):
    pass

class OrganizationInDB(OrganizationBase):
    org_id: UUID
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    is_deleted: Optional[bool]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    delete_reason: Optional[str]

    class Config:
        orm_mode = True