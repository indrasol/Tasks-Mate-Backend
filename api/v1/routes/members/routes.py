from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from models.schemas.member import *
from services import member as member_service
from core.db.async_session import get_db_session
from services.auth_handler import get_current_user

router = APIRouter(prefix="/api", tags=["Members"])


@router.get("/organizations/{org_id}/members")
async def list_members(
    org_id: str,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await member_service.list_members(db, org_id)


@router.post("/organizations/{org_id}/invite", response_model=InviteOut)
async def invite(
    org_id: str,
    invite: InviteCreate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await member_service.invite_member(db, org_id, invite.email, invite.role)


@router.post("/organizations/{org_id}/invite/resend")
async def resend(
    org_id: str,
    body: ResendInvite,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await member_service.resend_invite(db, body.invite_id)


@router.delete("/organizations/{org_id}/invite/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel(
    org_id: str,
    invite_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    await member_service.cancel_invite(db, invite_id)


@router.get("/organizations/{org_id}/invite/verify", response_model=VerifyInviteResponse)
async def verify(
    org_id: str,
    token: str,
    db: AsyncSession = Depends(get_db_session)
):
    return await member_service.verify_invite(db, token)


@router.post("/organizations/{org_id}/invite/accept")
async def accept(
    org_id: str,
    data: AcceptInvite,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await member_service.accept_invite(db, data.token, user["user_id"])


@router.delete("/organizations/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove(
    org_id: str,
    user_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    await member_service.remove_member(db, org_id, user_id)


@router.patch("/organizations/{org_id}/members/{user_id}/role")
async def change_role(
    org_id: str,
    user_id: UUID,
    data: ChangeRole,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await member_service.update_member_role(db, org_id, user_id, data.role)
