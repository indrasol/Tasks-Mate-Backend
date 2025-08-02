from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from models.enums import InviteStatusEnum

class OrganizationInviteBase(BaseModel):
    org_id: UUID = Field(..., description="Organization ID (UUID)", example="a1b2c3d4-5678-1234-9abc-def012345678")
    email: str = Field(..., description="Invitee's email", example="invitee@example.com")
    designation: Optional[UUID] = Field(None, description="Designation ID (UUID)", example="d1e2f3g4-5678-1234-9abc-def012345678")
    role: Optional[UUID] = Field(None, description="Role ID (UUID)", example="r1e2f3g4-5678-1234-9abc-def012345678")
    invited_by: Optional[UUID] = Field(None, description="Inviter's User ID (UUID)", example="b3c1e2d4-1234-5678-9abc-def012345678")
    invite_status: Optional[InviteStatusEnum] = Field(InviteStatusEnum.PENDING, description="Status of the invite", example=InviteStatusEnum.PENDING)
    sent_at: Optional[datetime] = Field(None, description="When the invite was sent")
    expires_at: Optional[datetime] = Field(None, description="When the invite expires")
    is_cancelled: Optional[bool] = Field(False, description="Is the invite cancelled?", example=False)
    cancel_date: Optional[datetime] = Field(None, description="When the invite was cancelled")

class OrganizationInviteCreate(OrganizationInviteBase):
    pass

class OrganizationInviteUpdate(OrganizationInviteBase):
    pass

class OrganizationInviteInDB(OrganizationInviteBase):
    id: UUID
    created_at: Optional[datetime] = Field(default=None, description="Created timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last updated timestamp")
    accepted_by: Optional[UUID] = Field(default=None, description="User who accepted the invite")
    accepted_at: Optional[datetime] = Field(default=None, description="When the invite was accepted")
    class Config:
        orm_mode = True