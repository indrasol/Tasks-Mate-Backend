from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class OrganizationMemberBase(BaseModel):
    user_id: UUID
    org_id: UUID
    designation: Optional[UUID]
    role: Optional[UUID]
    invited_by: Optional[UUID]
    is_active: Optional[bool]
    invited_at: Optional[datetime]
    accepted_at: Optional[datetime]
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    delete_reason: Optional[str]
    deleted_by: Optional[UUID]

class OrganizationMemberCreate(OrganizationMemberBase):
    pass

class OrganizationMemberUpdate(OrganizationMemberBase):
    pass

class OrganizationMemberInDB(OrganizationMemberBase):
    class Config:
        orm_mode = True