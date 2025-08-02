from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class RoleBase(BaseModel):
    name: str = Field(..., description="Role name (USER-DEFINED)", example="admin")
    permissions: Optional[dict] = Field({}, description="Role permissions as JSON", example={"can_create": True})

class RoleCreate(RoleBase):
    pass

class RoleUpdate(RoleBase):
    pass

class RoleInDB(RoleBase):
    role_id: UUID
    updated_at: Optional[datetime]
    class Config:
        orm_mode = True