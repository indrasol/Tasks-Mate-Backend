from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class TaskAttachmentBase(BaseModel):
    task_id: str
    title: Optional[str]
    name: Optional[str]
    url: Optional[str]
    uploaded_by: Optional[UUID]
    uploaded_at: Optional[datetime]
    deleted_at: Optional[datetime]
    deleted_by: Optional[UUID]
    is_inline: Optional[bool]

class TaskAttachmentCreate(TaskAttachmentBase):
    pass

class TaskAttachmentUpdate(TaskAttachmentBase):
    pass

class TaskAttachmentInDB(TaskAttachmentBase):
    attachment_id: UUID

    class Config:
        orm_mode = True