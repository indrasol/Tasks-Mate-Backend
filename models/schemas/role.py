from pydantic import BaseModel, validator
from typing import Optional
from uuid import UUID
from datetime import datetime

ALLOWED_ROLES = ["owner", "admin", "member"]

class RoleBase(BaseModel):
    name: str
    permissions: Optional[dict]

    @validator("name")
    def validate_role(cls, v):
        if v not in ALLOWED_ROLES:
            raise ValueError(f"Role must be one of {ALLOWED_ROLES}")
        return v

class RoleCreate(RoleBase):
    pass

class RoleUpdate(RoleBase):
    pass

class RoleInDB(RoleBase):
    role_id: UUID
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True