from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class OrganizationBase(BaseModel):
    name: str = Field(..., description="Organization name", example="Acme Corp")
    description: Optional[str] = Field(None, description="Description of the organization", example="A global tech company.")
    logo: Optional[str] = Field(None, description="Logo URL", example="https://example.com/logo.png")
    email: Optional[str] = Field(None, description="Contact email", example="info@acme.com")
    metadata: Optional[dict] = Field({}, description="Additional metadata", example={"industry": "tech"})

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(OrganizationBase):
    pass

class OrganizationInDB(OrganizationBase):
    org_id: UUID
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    is_deleted: Optional[bool]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    delete_reason: Optional[str]
    access_status: Optional[str] = Field(None, description="Access status: 'member' or 'invite'")
    class Config:
        orm_mode = True