from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class CompanySize(str, Enum):
    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"

class CoreValue(BaseModel):
    id: Optional[str] = None
    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    icon: Optional[str] = Field(default="star", max_length=50)
    order: int = Field(default=1, ge=1, le=20)
    created_at: Optional[datetime] = None

class OrganizationProfileBase(BaseModel):
    vision: Optional[str] = Field(None, max_length=1000)
    mission: Optional[str] = Field(None, max_length=1000)
    core_values: List[CoreValue] = Field(default_factory=list, max_items=10)
    company_culture: Optional[str] = Field(None, max_length=2000)
    founding_year: Optional[int] = Field(None, ge=1800, le=2030)
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[CompanySize] = None
    headquarters: Optional[str] = Field(None, max_length=200)
    website_url: Optional[str] = Field(None, max_length=500)
    sustainability_goals: Optional[str] = Field(None, max_length=1500)
    diversity_commitment: Optional[str] = Field(None, max_length=1500)
    community_involvement: Optional[str] = Field(None, max_length=1500)

    @validator('core_values')
    def validate_core_values(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 core values allowed')
        # Ensure unique titles
        titles = [value.title for value in v]
        if len(titles) != len(set(titles)):
            raise ValueError('Core value titles must be unique')
        return v

    @validator('website_url')
    def validate_website_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            return f'https://{v}'
        return v

class OrganizationProfileCreate(OrganizationProfileBase):
    pass

class OrganizationProfileUpdate(OrganizationProfileBase):
    pass

class OrganizationProfileResponse(OrganizationProfileBase):
    id: str
    org_id: str
    created_by: Optional[str]
    last_updated_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
