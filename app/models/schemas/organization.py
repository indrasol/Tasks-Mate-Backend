from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models.enums import RoleEnum

class OrganizationBase(BaseModel):
    name: str = Field(..., description="Organization name", example="Acme Corp")
    description: str = Field(None, description="Description of the organization", example="A global tech company.")
    # List of designation names available within this organization. This is stored as a text[] column in Supabase.
    designations: Optional[List[str]] = Field(default_factory=list, description="List of designation names available in this organization")
    logo: Optional[str] = Field(None, description="Logo URL", example="https://example.com/logo.png")
    email: Optional[str] = Field(None, description="Contact email", example="info@acme.com")
    plan: Optional[str] = Field(None, description="Subscription plan", example="pro")
    role: Optional[RoleEnum] = Field(RoleEnum.OWNER, description="Role of the current user in the organization", example="owner")
    metadata: Optional[dict] = Field({}, description="Additional metadata", example={"industry": "tech"})
    designation: Optional[str] = Field(None, description="Single designation chosen during organization creation")

class OrgCard(BaseModel):
    """Simplified organization model for card display"""
    org_id: str = Field(..., description="Organization ID", example="O123456")
    name: str = Field(..., description="Organization name", example="Acme Corp")
    description: str = Field(None, description="Description of the organization", example="A global tech company.")
    role: str = Field("owner", description="Role of the current user in the organization", example="owner")
    designation: Optional[str] = Field(None, description="User's designation in the organization")
    project_count: int = Field(0, description="Number of projects under the organization")
    member_count: int = Field(0, description="Number of members in the organization")
    created_by: Optional[str] = Field(None, description="Username of the creator")
    created_at: Optional[datetime] = Field(None, description="When the organization was created")
    is_invite: Optional[bool] = Field(None, description="Is Organization Invite")
    invitation_id: Optional[str] = Field(None, description="Invitation ID", example="O123456")

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(OrganizationBase):
    pass

class OrganizationInDB(OrganizationBase):
    org_id: str
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    is_deleted: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    delete_reason: Optional[str] = None
    project_count: int = Field(0, description="Number of projects under the organization")
    designations: List[str] = Field(default_factory=list, description="List of designation names available in this organization")
    role: str = Field("owner", description="Role of the current user in the organization")
    access_status: Optional[str] = None
    class Config:
        orm_mode = True


class OrganizationDelete(BaseModel):
    delete_reason: Optional[str] = None