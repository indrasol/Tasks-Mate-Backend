from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class ProjectMemberBase(BaseModel):
    project_id: str = Field(..., description="Project ID (text)", example="project-1234")
    user_id: UUID = Field(..., description="User ID (UUID)", example="b3c1e2d4-1234-5678-9abc-def012345678")
    username: Optional[str] = Field(None, description="Username of the member", example="john_doe")
    designation: Optional[str] = Field(None, description="Designation name", example="developer")
    role: Optional[str] = Field(None, description="Role name", example="owner")
    created_by: Optional[str] = Field(None, description="Who created the membership (username)")
    updated_by: Optional[str] = Field(None, description="Who last updated the membership (username)")
    is_active: Optional[bool] = Field(True, description="Is the member active?", example=True)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="When the member was deleted")
    delete_reason: Optional[str] = Field(None, description="Reason for deletion")
    # deleted_by: Optional[UUID] = Field(None, description="Who deleted the member")

class ProjectMemberCreate(ProjectMemberBase):
    pass

class ProjectMemberUpdate(ProjectMemberBase):
    pass

class ProjectMemberInDB(ProjectMemberBase):
    class Config:
        orm_mode = True