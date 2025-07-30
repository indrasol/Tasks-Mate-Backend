from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from models.schemas.task_comments import *
from services import task_comments as task_comment_service
from core.db.async_session import get_db_session
from services.auth_handler import get_current_user

router = APIRouter(prefix="/api", tags=["Task Comments"])


@router.post("/tasks/{task_id}/comments", response_model=TaskCommentOut, status_code=status.HTTP_201_CREATED)
async def post_comment(
    task_id: str,
    data: TaskCommentCreate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await task_comment_service.add_comment(db, task_id, user["id"], data.content)


@router.get("/tasks/{task_id}/comments", response_model=list[TaskCommentOut])
async def get_comments(
    task_id: str,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await task_comment_service.list_comments(db, task_id)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    await task_comment_service.delete_comment(db, comment_id, user["id"])
