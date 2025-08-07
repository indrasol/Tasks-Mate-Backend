from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from app.models.enums import TaskStatusEnum, PriorityEnum

class TaskBase(BaseModel):
    project_id: str = Field(..., description="Project ID (text)", example="project-1234")
    sub_tasks: Optional[List[str]] = Field([], description="List of sub-task IDs", example=["task-5678"])
    dependencies: Optional[List[str]] = Field([], description="List of dependency task IDs", example=["task-4321"])
    title: str = Field(..., description="Task title", example="Implement Login")
    description: Optional[str] = Field(None, description="Task description", example="Implement OAuth2 login flow.")
    status: Optional[TaskStatusEnum] = Field(TaskStatusEnum.NOT_STARTED, description="Task status", example=TaskStatusEnum.NOT_STARTED)
    assignee_id: Optional[str] = Field(None, description="Assignee user ID", example="b3c1e2d4-1234-5678-9abc-def012345678")
    due_date: Optional[date] = Field(None, description="Due date", example="2024-08-01")
    priority: Optional[PriorityEnum] = Field(PriorityEnum.NONE, description="Task priority", example=PriorityEnum.HIGH)
    tags: Optional[List[str]] = Field([], description="List of tags", example=["backend", "auth"])
    metadata: Optional[List[dict]] = Field([], description="Additional metadata", example=[{"field": "status", "old": "not_started", "new": "in_progress"}])
    created_by: Optional[str] = Field(None, description="Who created the task")
    updated_by: Optional[str] = Field(None, description="Who last updated the task")

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    pass

class TaskInDB(TaskBase):
    task_id: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    class Config:
        orm_mode = True