from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class TaskCommentCreate(BaseModel):
    content: str


class TaskCommentOut(BaseModel):
    id: UUID
    task_id: str
    user_id: UUID
    content: str
    created_at: datetime

    class Config:
        orm_mode = True
