from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class TaskHistoryBase(BaseModel):
    task_id: str = Field(..., description="Task ID (text)", example="task-1234")
    title: Optional[str] = Field(None, description="History title", example="Initial Version")
    metadata: Optional[List[dict]] = Field([], description="List of metadata JSON objects", example=[{"field": "status", "old": "not_started", "new": "in_progress"}])
    hash_id: Optional[str] = Field(None, description="Hash ID for versioning", example="abc123hash")
    updated_at: Optional[datetime] = Field(None, description="When the history was last updated")

class TaskHistoryCreate(TaskHistoryBase):
    pass

class TaskHistoryUpdate(TaskHistoryBase):
    pass

class TaskHistoryInDB(TaskHistoryBase):
    history_id: str
    created_by: str = Field(..., description="User ID of the creator", example="user-1234")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the history was created", example="2023-10-01T12:00:00Z")
    class Config:
        orm_mode = True