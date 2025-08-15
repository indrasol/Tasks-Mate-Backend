from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class ProjectResourceBase(BaseModel):
    project_id: str = Field(..., description="Project ID (text)", example="project-1234")
    project_name: str = Field(..., description="Project name", example="Project 1")
    resource_name: str = Field(..., description="Resource name", example="API Docs")
    resource_url: Optional[str] = Field(None, description="Resource URL", example="https://example.com/api-docs.pdf")
    resource_type: Optional[str] = Field(None, description="Type of resource", example="pdf")
    storage_path: Optional[str] = Field(None, description="Original File Storage Path")
    is_active: Optional[bool] = Field(True, description="Is the resource active?", example=True)
    created_by: Optional[str] = Field(None, description="Who created the resource")
    updated_by: Optional[str] = Field(None, description="Who last updated the resource")
    delete_reason: Optional[str] = Field(None, description="Reason for deletion")

class ProjectResourceCreate(ProjectResourceBase):
    pass

class ProjectResourceUpdate(BaseModel):
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    resource_name: Optional[str] = None
    resource_url: Optional[str] = None
    resource_type: Optional[str] = None
    is_active: Optional[bool] = True
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    delete_reason: Optional[str] = None

class ProjectResourceInDB(ProjectResourceBase):
    resource_id: str = Field(..., description="Resource ID", example="RE0001")
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    class Config:
        orm_mode = True