from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime, date

class ProjectBase(BaseModel):
    org_id: UUID
    name: str
    description: Optional[str]
    metadata: Optional[dict]
    status: Optional[str]
    priority: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    is_active: Optional[bool]
    delete_reason: Optional[str]

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    pass

class ProjectInDB(ProjectBase):
    project_id: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]

    class Config:
        orm_mode = True