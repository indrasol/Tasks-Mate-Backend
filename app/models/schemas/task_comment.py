from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class TaskCommentBase(BaseModel):
    task_id: str = Field(..., description="Task ID (text)", example="task-1234")
    title: Optional[str] = Field(None, description="Comment title", example="Initial Feedback")
    user_id: Optional[UUID] = Field(None, description="User ID (UUID)", example="b3c1e2d4-1234-5678-9abc-def012345678")
    content: str = Field(..., description="Comment content", example="Looks good, but needs more tests.")
    created_at: Optional[datetime] = Field(None, description="When the comment was created")
    updated_at: Optional[datetime] = Field(None, description="When the comment was last updated")

class TaskCommentCreate(TaskCommentBase):
    pass

class TaskCommentUpdate(TaskCommentBase):
    pass

class TaskCommentInDB(TaskCommentBase):
    comment_id: UUID
    class Config:
        orm_mode = True