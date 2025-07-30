from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from services.auth_handler import get_current_user
from models.schemas.project_team import *
from services import project_team as project_team_service
from core.db.async_session import get_db_session

router = APIRouter(prefix="/api", tags=["Project Team"])


@router.get("/projects/{project_id}/team", response_model=list[ProjectTeamMemberOut])
async def list_team(
    project_id: str,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await project_team_service.list_team_members(db, project_id)


@router.post("/projects/{project_id}/team", status_code=status.HTTP_201_CREATED)
async def add_member(
    project_id: str,
    member: ProjectTeamAdd,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await project_team_service.add_team_member(db, project_id, member.user_id, member.role)


@router.delete("/projects/{project_id}/team/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    project_id: str,
    user_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    await project_team_service.remove_team_member(db, project_id, user_id)


@router.patch("/projects/{project_id}/team/{user_id}/role")
async def update_role(
    project_id: str,
    user_id: UUID,
    data: ProjectTeamUpdateRole,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await project_team_service.update_team_role(db, project_id, user_id, data.role)
