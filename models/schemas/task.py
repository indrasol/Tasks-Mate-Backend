from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class TaskBase(BaseModel):
    title: str
    description: Optional[str]
    status: Optional[str] = "not_started"
    assignee_id: Optional[UUID]
    due_date: Optional[datetime]
    priority: Optional[str] = "none"
    tags: List[str] = []
    metadata: List[dict] = []


class TaskCreate(TaskBase):
    project_id: str
    task_id: str


class TaskUpdate(TaskBase):
    pass


class TaskInDB(TaskBase):
    task_id: str
    project_id: str
    sub_tasks: List[str] = []
    created_at: datetime

    class Config:
        orm_mode = True
