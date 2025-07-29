from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    org_id: str
    project_id: str


class ProjectUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]


class ProjectInDB(ProjectBase):
    id: str
    org_id: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


class ProjectListResponse(BaseModel):
    projects: List[ProjectInDB]
    total: int
    page: int
    limit: int
