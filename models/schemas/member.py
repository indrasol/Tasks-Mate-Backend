from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class MemberOut(BaseModel):
    id: UUID
    name: Optional[str]
    email: EmailStr
    role: str
    status: str = "active"

    class Config:
        orm_mode = True


class InviteCreate(BaseModel):
    email: EmailStr
    role: str


class InviteOut(BaseModel):
    invite_id: UUID
    email: EmailStr
    role: str
    status: str = "pending"

    class Config:
        orm_mode = True


class ResendInvite(BaseModel):
    invite_id: UUID


class AcceptInvite(BaseModel):
    token: str


class VerifyInviteResponse(BaseModel):
    valid: bool
    email: EmailStr
    org_id: UUID


class ChangeRole(BaseModel):
    role: str
