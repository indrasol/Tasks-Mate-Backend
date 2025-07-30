from fastapi import APIRouter, Depends, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from models.schemas.task_tags import *
from services import task_tags as tag_service
from core.db.async_session import get_db_session
from services.auth_handler import get_current_user

router = APIRouter(prefix="/api", tags=["Tags"])


@router.get("/tags", response_model=list[TagOut])
async def list_tags(
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await tag_service.list_tags(db)


@router.post("/tags", response_model=TagOut, status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: TagCreate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await tag_service.create_tag(db, name=data.name, color=data.color)


@router.patch("/tags/{tag_id}", response_model=TagOut)
async def update_tag(
    tag_id: UUID,
    data: TagUpdate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await tag_service.update_tag(db, tag_id, name=data.name, color=data.color)


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    await tag_service.delete_tag(db, tag_id)


@router.patch("/tasks/{task_id}/tags")
async def assign_tags(
    task_id: str,
    tag_ids: list[UUID],
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await tag_service.assign_tags_to_task(db, task_id, tag_ids)


@router.get("/tasks/{task_id}/tags", response_model=list[TagOut])
async def get_tags_for_task(
    task_id: str,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await tag_service.get_tags_for_task(db, task_id)
