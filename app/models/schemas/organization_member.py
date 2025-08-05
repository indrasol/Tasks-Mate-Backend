from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class OrganizationMemberBase(BaseModel):
    user_id: UUID = Field(..., description="User ID (UUID)", example="b3c1e2d4-1234-5678-9abc-def012345678")
    org_id: str = Field(..., description="Organization ID (UUID)", example="a1b2c3d4-5678-1234-9abc-def012345678")
    designation: Optional[str] = Field(None, description="Designation ID (UUID)", example="d1e2f3g4-5678-1234-9abc-def012345678")
    role: Optional[str] = Field(None, description="Role ID (UUID)", example="r1e2f3g4-5678-1234-9abc-def012345678")
    invited_by: Optional[str] = Field(None, description="Inviter's User ID (UUID)", example="b3c1e2d4-1234-5678-9abc-def012345678")
    is_active: Optional[bool] = Field(True, description="Is the member active?", example=True)
    invited_at: Optional[datetime] = Field(None, description="When the invite was sent")
    accepted_at: Optional[datetime] = Field(None, description="When the invite was accepted")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="When the member was deleted")
    delete_reason: Optional[str] = Field(None, description="Reason for deletion")
    deleted_by: Optional[str] = Field(None, description="Who deleted the member")

class OrganizationMemberCreate(OrganizationMemberBase):
    pass

class OrganizationMemberUpdate(OrganizationMemberBase):
    pass

class OrganizationMemberInDB(OrganizationMemberBase):
    class Config:
        orm_mode = True