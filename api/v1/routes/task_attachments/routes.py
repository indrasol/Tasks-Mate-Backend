from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from models.schemas.task_attachments import *
from services import task_attachments as task_attachment_service
from core.db.async_session import get_db_session
from services.auth_handler import get_current_user

router = APIRouter(prefix="/api", tags=["Task Attachments"])


@router.post("/tasks/{task_id}/attachments", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    task_id: str,
    data: AttachmentUpload,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await task_attachment_service.upload_attachment(db, task_id, user["id"], data.file_name, data.file_url)


@router.get("/tasks/{task_id}/attachments", response_model=list[AttachmentOut])
async def list_attachments(
    task_id: str,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await task_attachment_service.list_attachments(db, task_id)


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    await task_attachment_service.delete_attachment(db, attachment_id, user["id"])
