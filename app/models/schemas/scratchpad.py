from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class ScratchpadCreate(BaseModel):
    org_id: str = Field(..., description="Organization ID")
    content: str = Field("", description="Scratchpad content")


class ScratchpadInDB(ScratchpadCreate):
    user_id: UUID
    org_name: Optional[str] = None
    user_name: Optional[str] = None
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
