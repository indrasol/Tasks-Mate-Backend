from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class ProjectResourceBase(BaseModel):
    project_id: str = Field(..., description="Project ID (text)", example="project-1234")
    name: str = Field(..., description="Resource name", example="API Docs")
    url: Optional[str] = Field(None, description="Resource URL", example="https://example.com/api-docs.pdf")
    resource_type: Optional[str] = Field(None, description="Type of resource", example="pdf")
    is_active: Optional[bool] = Field(True, description="Is the resource active?", example=True)
    created_by: Optional[UUID] = Field(None, description="Who created the resource")
    updated_by: Optional[UUID] = Field(None, description="Who last updated the resource")
    delete_reason: Optional[str] = Field(None, description="Reason for deletion")

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