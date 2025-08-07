from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from app.models.enums import ProjectStatusEnum, PriorityEnum
from app.models.schemas.project_stats import ProjectStatsBase

from typing import List

class ProjectBase(BaseModel):
    org_id: str = Field(..., description="Organization ID (UUID)", example="a1b2c3d4-5678-1234-9abc-def012345678")
    name: str = Field(..., description="Project name", example="Website Redesign")
    description: Optional[str] = Field(None, description="Project description", example="Redesign the company website.")
    metadata: Optional[dict] = Field({}, description="Additional metadata", example={"budget": 10000})
    status: Optional[ProjectStatusEnum] = Field(ProjectStatusEnum.NOT_STARTED, description="Project status", example=ProjectStatusEnum.NOT_STARTED)
    priority: Optional[PriorityEnum] = Field(PriorityEnum.NONE, description="Project priority", example=PriorityEnum.HIGH)
    start_date: Optional[date] = Field(None, description="Start date", example="2024-07-01")
    end_date: Optional[date] = Field(None, description="End date", example="2024-12-31")
    created_by: Optional[str] = Field(None, description="Who created the project")
    updated_by: Optional[str] = Field(None, description="Who last updated the project")
    is_active: Optional[bool] = Field(True, description="Is the project active?", example=True)
    delete_reason: Optional[str] = Field(None, description="Reason for deletion")
    owner: Optional[str] = Field(None, description="User name of the project owner")
    team_members: Optional[List[str]] = Field(default_factory=list, description="List of user names to add as members")

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    org_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[dict] = None
    status: Optional[ProjectStatusEnum] = None
    priority: Optional[PriorityEnum] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    delete_reason: Optional[str] = None
    owner: Optional[str] = None
    team_members: Optional[List[str]] = None

    class Config:
        orm_mode = True

class ProjectInDB(ProjectBase):
    project_id: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    class Config:
        orm_mode = True

class ProjectCard(ProjectBase):
    """Simplified project representation for dashboard cards."""
    project_id: str = Field(..., description="Project ID", example="P00001")
    tasks_total: int = Field(..., description="Total number of tasks in the project", example=25)
    tasks_completed: int = Field(..., description="Number of completed tasks", example=15)
    progress_percent: Decimal = Field(..., description="Project completion percentage", example=60.0)
