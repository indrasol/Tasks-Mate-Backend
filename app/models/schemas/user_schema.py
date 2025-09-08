from pydantic import BaseModel, Field
from typing import Optional


class UserAvatarResponse(BaseModel):
    """Response schema for user avatar upload"""
    avatar_url: str = Field(..., description="URL to the uploaded avatar")


class UserAvatarRequest(BaseModel):
    """Request schema for user avatar fetch"""
    user_id: Optional[str] = Field(None, description="User ID to fetch avatar for. Uses current user if not provided")
