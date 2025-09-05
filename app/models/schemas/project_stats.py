from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

class ProjectStatsBase(BaseModel):
    project_id: str = Field(..., description="Project ID", example="project-1234")
    tasks_total: int = Field(..., description="Total number of tasks in the project", example=25)
    tasks_completed: int = Field(..., description="Number of completed tasks", example=15)
    progress_percent: Decimal = Field(..., description="Project completion percentage", example=60.0)
    team_members: int = Field(..., description="Number of members in the project", example=5)
    days_left: int = Field(..., description="Days remaining until end_date", example=30)
    duration_days: Optional[int] = Field(None, description="Project duration in days", example=120)
    bugs_total: Optional[int] = Field(None, description="Total number of bugs in the project", example=5)

class ProjectStatsInDB(ProjectStatsBase):
    class Config:
        orm_mode = True 