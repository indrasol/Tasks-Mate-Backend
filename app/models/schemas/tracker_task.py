from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TrackerTaskBase(BaseModel):
    created_by: Optional[str] = Field(None, description="Who created the task")
    updated_by: Optional[str] = Field(None, description="Who last updated the task")
    bug_id: Optional[str] = Field(None, description="Bug ID (text)", example="B1234")
    tracker_id: Optional[str] = Field(None, description="Tracker ID (text)", example="TR1234")
    task_id: Optional[str] = Field(None, description="Task ID (text)", example="TR1234")  

class TrackerTaskCreate(TrackerTaskBase):
    pass

class TrackerTaskInDB(TrackerTaskBase):
    task_id: str
    created_at: Optional[datetime] = Field(None, description="Tracker ID (text)", example="TR1234")
    updated_at: Optional[datetime] = Field(None, description="Tracker ID (text)", example="TR1234")
    class Config:
        orm_mode = True
