from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class TaskCommentBase(BaseModel):
    task_id: str = Field(..., description="Task ID (text)", example="task-1234")
    task_title: Optional[str] = Field(None, description="Task title snapshot at time of comment", example="Implement Login")
    created_by: Optional[str] = Field(None, description="User ID (UUID)", example="b3c1e2d4-1234-5678-9abc-def012345678")
    # DB may contain both `comment` and `content`. Accept either; at least one required at route level.
    comment: Optional[str] = Field(None, description="Legacy/alternative comment field")
    content: Optional[str] = Field(None, description="Comment content", example="Looks good, but needs more tests.")
    parent_comment_id: Optional[str] = Field(None, description="ID of the parent comment if this is a reply")
    created_at: Optional[datetime] = Field(None, description="When the comment was created")
    updated_at: Optional[datetime] = Field(None, description="When the comment was last updated")

class TaskCommentCreate(TaskCommentBase):
    pass

class TaskCommentUpdate(BaseModel):
    task_id: Optional[str] = Field(None, description="Task ID (text)")
    task_title: Optional[str] = Field(None, description="Task title snapshot at time of comment")
    created_by: Optional[str] = Field(None, description="User ID (UUID)")
    comment: Optional[str] = Field(None, description="Legacy/alternative comment field")
    content: Optional[str] = Field(None, description="Comment content")
    created_at: Optional[datetime] = Field(None, description="When the comment was created")
    updated_at: Optional[datetime] = Field(None, description="When the comment was last updated")

class TaskCommentInDB(TaskCommentBase):
    comment_id: str
    replies: List['TaskCommentInDB'] = Field(default_factory=list, description="List of reply comments")
    
    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }