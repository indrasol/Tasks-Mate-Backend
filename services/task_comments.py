from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.db_schemas.db_schema_models import TaskComment
from uuid import UUID
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


async def add_comment(db: AsyncSession, task_id: str, user_id: UUID, content: str):
    comment = TaskComment(task_id=task_id, user_id=user_id, content=content)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


async def list_comments(db: AsyncSession, task_id: str):
    result = await db.execute(
        select(TaskComment).where(TaskComment.task_id == task_id).order_by(TaskComment.created_at)
    )
    return result.scalars().all()


async def delete_comment(db: AsyncSession, comment_id: UUID, user_id: UUID):
    comment = await db.get(TaskComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can't delete this comment")
    await db.delete(comment)
    await db.commit()
