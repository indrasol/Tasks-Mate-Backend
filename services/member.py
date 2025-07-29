from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from models.db_schemas.db_schema_models import OrganizationInvite, OrganizationMember, User
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


async def list_members(db: AsyncSession, org_id: str):
    result = await db.execute(
        select(OrganizationMember, User)
        .join(User, User.id == OrganizationMember.user_id)
        .where(OrganizationMember.org_id == org_id)
    )
    members = result.all()
    return [
        {
            "id": m.OrganizationMember.user_id,
            "name": m.User.name,
            "email": m.User.email,
            "role": m.OrganizationMember.role,
            "status": "active",
        }
        for m in members
    ]


async def invite_member(db: AsyncSession, org_id: str, email: str, role: str):
    invite = OrganizationInvite(
        email=email,
        role=role,
        org_id=org_id,
        status="pending"
    )
    db.add(invite)
    try:
        await db.commit()
        await db.refresh(invite)
        return {
            "invite_id": invite.invite_id,
            "email": invite.email,
            "role": invite.role,
            "status": invite.status
        }
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Failed to invite member")
        raise HTTPException(status_code=500, detail="Could not create invite")


async def resend_invite(db: AsyncSession, invite_id: UUID):
    invite = await db.get(OrganizationInvite, invite_id)
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    # Here you'd trigger an email resend if needed.
    return {"resent": True}


async def cancel_invite(db: AsyncSession, invite_id: UUID):
    invite = await db.get(OrganizationInvite, invite_id)
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    await db.delete(invite)
    await db.commit()


async def verify_invite(db: AsyncSession, token: str):
    # Assuming token is just invite_id for now (simplified)
    invite = await db.get(OrganizationInvite, UUID(token))
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid token")
    return {
        "valid": True,
        "email": invite.email,
        "org_id": invite.org_id
    }


async def accept_invite(db: AsyncSession, token: str, user_id: UUID):
    invite = await db.get(OrganizationInvite, UUID(token))
    if not invite or invite.status != "pending":
        raise HTTPException(status_code=404, detail="Invalid or expired invite")

    member = OrganizationMember(
        org_id=invite.org_id,
        user_id=user_id,
        role=invite.role
    )
    db.add(member)
    invite.status = "accepted"
    await db.commit()
    return {
        "accepted": True,
        "user": {
            "id": user_id,
            "email": invite.email
        }
    }


async def remove_member(db: AsyncSession, org_id: str, user_id: UUID):
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.org_id == org_id,
            OrganizationMember.user_id == user_id
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    await db.delete(member)
    await db.commit()


async def update_member_role(db: AsyncSession, org_id: str, user_id: UUID, role: str):
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.org_id == org_id,
            OrganizationMember.user_id == user_id
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.role = role
    await db.commit()
    return {"id": user_id, "role": role}
