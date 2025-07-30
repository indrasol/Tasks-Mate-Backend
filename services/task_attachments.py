from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.db_schemas.db_schema_models import TaskAttachment
from uuid import UUID
from fastapi import HTTPException


async def upload_attachment(db: AsyncSession, task_id: str, user_id: UUID, file_name: str, file_url: str):
    attachment = TaskAttachment(
        task_id=task_id,
        user_id=user_id,
        file_name=file_name,
        file_url=file_url
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return attachment


async def list_attachments(db: AsyncSession, task_id: str):
    result = await db.execute(
        select(TaskAttachment).where(TaskAttachment.task_id == task_id).order_by(TaskAttachment.uploaded_at.desc())
    )
    return result.scalars().all()


async def delete_attachment(db: AsyncSession, attachment_id: UUID, user_id: UUID):
    attachment = await db.get(TaskAttachment, attachment_id)
    if not attachment or attachment.user_id != user_id:
        raise HTTPException(status_code=404, detail="Attachment not found or permission denied")

    await db.delete(attachment)
    await db.commit()
