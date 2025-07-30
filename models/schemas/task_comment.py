from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class TaskCommentBase(BaseModel):
    task_id: str
    title: Optional[str]
    user_id: Optional[UUID]
    content: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class TaskCommentCreate(TaskCommentBase):
    pass

class TaskCommentUpdate(TaskCommentBase):
    pass

class TaskCommentInDB(TaskCommentBase):
    comment_id: UUID

    class Config:
        orm_mode = True