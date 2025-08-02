from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

class ProjectStatsBase(BaseModel):
    project_id: str = Field(..., description="Project ID", example="project-1234")
    tasks_total: int = Field(..., description="Total number of tasks in the project", example=25)
    tasks_completed: int = Field(..., description="Number of completed tasks", example=15)
    progress_percent: Decimal = Field(..., description="Project completion percentage", example=60.0)

class ProjectStatsInDB(ProjectStatsBase):
    class Config:
        orm_mode = True 