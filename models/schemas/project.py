from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from models.enums import ProjectStatusEnum, PriorityEnum
from models.schemas.project_stats import ProjectStatsBase

class ProjectBase(BaseModel):
    org_id: UUID = Field(..., description="Organization ID (UUID)", example="a1b2c3d4-5678-1234-9abc-def012345678")
    name: str = Field(..., description="Project name", example="Website Redesign")
    description: Optional[str] = Field(None, description="Project description", example="Redesign the company website.")
    metadata: Optional[dict] = Field({}, description="Additional metadata", example={"budget": 10000})
    status: Optional[ProjectStatusEnum] = Field(ProjectStatusEnum.NOT_STARTED, description="Project status", example=ProjectStatusEnum.NOT_STARTED)
    priority: Optional[PriorityEnum] = Field(PriorityEnum.NONE, description="Project priority", example=PriorityEnum.HIGH)
    start_date: Optional[date] = Field(None, description="Start date", example="2024-07-01")
    end_date: Optional[date] = Field(None, description="End date", example="2024-12-31")
    created_by: Optional[UUID] = Field(None, description="Who created the project")
    updated_by: Optional[UUID] = Field(None, description="Who last updated the project")
    is_active: Optional[bool] = Field(True, description="Is the project active?", example=True)
    delete_reason: Optional[str] = Field(None, description="Reason for deletion")

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

class ProjectCard(ProjectBase):
    # project_stats: ProjectStatsBase
    tasks_total: int = Field(..., description="Total number of tasks in the project", example=25)
    tasks_completed: int = Field(..., description="Number of completed tasks", example=15)
    progress_percent: Decimal = Field(..., description="Project completion percentage", example=60.0)