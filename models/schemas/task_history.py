from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class TaskHistoryBase(BaseModel):
    task_id: str
    title: Optional[str]
    metadata: Optional[List[dict]]
    hash_id: Optional[str]
    updated_at: Optional[datetime]

class TaskHistoryCreate(TaskHistoryBase):
    pass

class TaskHistoryUpdate(TaskHistoryBase):
    pass

class TaskHistoryInDB(TaskHistoryBase):
    history_id: UUID

    class Config:
        orm_mode = True