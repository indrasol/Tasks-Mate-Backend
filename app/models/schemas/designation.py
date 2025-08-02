from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class DesignationBase(BaseModel):
    name: str = Field(..., description="Designation name (USER-DEFINED)", example="Lead Developer")
    metadata: Optional[dict] = Field({}, description="Additional metadata", example={"department": "Engineering"})

class DesignationCreate(DesignationBase):
    pass

class DesignationUpdate(DesignationBase):
    pass

class DesignationInDB(DesignationBase):
    designation_id: UUID
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    class Config:
        orm_mode = True