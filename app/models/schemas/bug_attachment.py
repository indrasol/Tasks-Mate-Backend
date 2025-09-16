from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class BugAttachmentBase(BaseModel):
    bug_id: str = Field(..., description="Bug ID (text)", example="bug-1234")
    title: Optional[str] = Field(None, description="Attachment title", example="Design Doc")
    name: Optional[str] = Field(None, description="Attachment file name", example="design.pdf")
    url: Optional[str] = Field(None, description="Attachment URL", example="https://example.com/design.pdf")
    uploaded_by: Optional[str] = Field(None, description="Who uploaded the attachment")
    uploaded_at: Optional[datetime] = Field(None, description="When the attachment was uploaded")
    deleted_at: Optional[datetime] = Field(None, description="When the attachment was deleted")
    deleted_by: Optional[str] = Field(None, description="Who deleted the attachment")
    is_inline: Optional[bool] = Field(False, description="Is the attachment inline?", example=False)

class BugAttachmentCreate(BugAttachmentBase):
    pass

class BugAttachmentUpdate(BugAttachmentBase):
    pass

class BugAttachmentInDB(BugAttachmentBase):
    attachment_id: str
    class Config:
        orm_mode = True