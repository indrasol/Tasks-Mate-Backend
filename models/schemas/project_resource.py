from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class ProjectResourceBase(BaseModel):
    project_id: str
    name: str
    url: Optional[str]
    resource_type: Optional[str]
    is_active: Optional[bool]
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    delete_reason: Optional[str]

class ProjectResourceCreate(ProjectResourceBase):
    pass

class ProjectResourceUpdate(ProjectResourceBase):
    pass

class ProjectResourceInDB(ProjectResourceBase):
    resource_id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]

    class Config:
        orm_mode = True