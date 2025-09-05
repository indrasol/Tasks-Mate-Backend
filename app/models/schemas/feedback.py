# models/feedback_model.py
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class Feedback(BaseModel):
    id: Optional[UUID] = None
    module: str
    type: str
    message: str
    submitted_by: Optional[UUID] = None
    submitted_at: Optional[str] = None
