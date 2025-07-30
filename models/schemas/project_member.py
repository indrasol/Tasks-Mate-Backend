from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class ProjectMemberBase(BaseModel):
    project_id: str
    user_id: UUID
    designation: Optional[UUID]
    role: Optional[UUID]
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    is_active: Optional[bool]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    delete_reason: Optional[str]

class ProjectMemberCreate(ProjectMemberBase):
    pass

class ProjectMemberUpdate(ProjectMemberBase):
    pass

class ProjectMemberInDB(ProjectMemberBase):
    class Config:
        orm_mode = True