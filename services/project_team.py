from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from models.db_schemas.db_schema_models import ProjectTeam, User
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


async def list_team_members(db: AsyncSession, project_id: str):
    result = await db.execute(
        select(ProjectTeam, User)
        .join(User, User.id == ProjectTeam.user_id)
        .where(ProjectTeam.project_id == project_id)
    )
    members = result.all()
    return [
        {
            "id": m.ProjectTeam.user_id,
            "name": m.User.name,
            "email": m.User.email,
            "role": m.ProjectTeam.role,
        }
        for m in members
    ]


async def add_team_member(db: AsyncSession, project_id: str, user_id: UUID, role: str):
    exists = await db.get(ProjectTeam, (project_id, user_id))
    if exists:
        raise HTTPException(status_code=409, detail="User already in project team")

    member = ProjectTeam(project_id=project_id, user_id=user_id, role=role)
    db.add(member)
    try:
        await db.commit()
        return {"id": user_id, "role": role}
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Failed to add project team member")
        raise HTTPException(status_code=500, detail="Could not add team member")


async def remove_team_member(db: AsyncSession, project_id: str, user_id: UUID):
    member = await db.get(ProjectTeam, (project_id, user_id))
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    await db.delete(member)
    await db.commit()


async def update_team_role(db: AsyncSession, project_id: str, user_id: UUID, role: str):
    member = await db.get(ProjectTeam, (project_id, user_id))
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.role = role
    await db.commit()
    return {"id": user_id, "role": role}
