from fastapi import APIRouter, Depends, status, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from models.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectInDB,
    ProjectListResponse
)
from services import project as project_service
from services.auth_handler import get_current_user
from core.db.async_session import get_db_session

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    search: Optional[str] = "",
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    skip = (page - 1) * limit
    return await project_service.get_projects(db, skip=skip, limit=limit, search=search)


@router.post("/", response_model=ProjectInDB, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await project_service.create_project(db, project_data=project, user_id=UUID(user["sub"]))


@router.get("/{project_id}", response_model=ProjectInDB)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await project_service.get_project(db, project_id)


@router.put("/{project_id}", response_model=ProjectInDB)
async def update_project(
    project_id: str,
    update: ProjectUpdate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await project_service.update_project(db, project_id, update)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    await project_service.delete_project(db, project_id)


@router.post("/{project_id}/archive")
async def archive_project(
    project_id: str,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await project_service.archive_project(db, project_id)


@router.post("/{project_id}/restore")
async def restore_project(
    project_id: str,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await project_service.restore_project(db, project_id)
