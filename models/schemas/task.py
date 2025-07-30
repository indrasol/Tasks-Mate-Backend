from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date

class TaskBase(BaseModel):
    project_id: str
    sub_tasks: Optional[List[str]]
    dependencies: Optional[List[str]]
    title: str
    description: Optional[str]
    status: Optional[str]
    assignee_id: Optional[UUID]
    due_date: Optional[date]
    priority: Optional[str]
    tags: Optional[List[str]]
    metadata: Optional[List[dict]]
    created_by: Optional[UUID]
    updated_by: Optional[UUID]

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