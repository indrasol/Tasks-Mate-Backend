from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class OrganizationInviteBase(BaseModel):
    org_id: UUID
    email: str
    designation: Optional[UUID]
    role: Optional[UUID]
    invited_by: Optional[UUID]
    invite_status: Optional[str]
    sent_at: Optional[datetime]
    expires_at: Optional[datetime]
    is_cancelled: Optional[bool]
    cancel_date: Optional[datetime]

class OrganizationInviteCreate(OrganizationInviteBase):
    pass

class OrganizationInviteUpdate(OrganizationInviteBase):
    pass

class OrganizationInviteInDB(OrganizationInviteBase):
    id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True