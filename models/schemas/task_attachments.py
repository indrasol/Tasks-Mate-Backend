from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class AttachmentUpload(BaseModel):
    file_name: str
    file_url: str


class AttachmentOut(BaseModel):
    id: UUID
    task_id: str
    user_id: UUID
    file_name: str
    file_url: str
    uploaded_at: datetime

    class Config:
        orm_mode = True
