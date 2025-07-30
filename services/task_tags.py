from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from models.db_schemas.db_schema_models import Tag, task_tags_table, Task
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


async def list_tags(db: AsyncSession):
    result = await db.execute(select(Tag))
    return result.scalars().all()


async def create_tag(db: AsyncSession, name: str, color: str):
    tag = Tag(name=name, color=color)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


async def update_tag(db: AsyncSession, tag_id: UUID, name: str = None, color: str = None):
    tag = await db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    if name:
        tag.name = name
    if color is not None:
        tag.color = color

    await db.commit()
    return tag


async def delete_tag(db: AsyncSession, tag_id: UUID):
    tag = await db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    await db.delete(tag)
    await db.commit()


async def assign_tags_to_task(db: AsyncSession, task_id: str, tag_ids: list[UUID]):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.execute(task_tags_table.delete().where(task_tags_table.c.task_id == task_id))

    for tag_id in tag_ids:
        await db.execute(task_tags_table.insert().values(task_id=task_id, tag_id=tag_id))

    await db.commit()
    return {"id": task_id, "tags": tag_ids}


async def get_tags_for_task(db: AsyncSession, task_id: str):
    query = (
        select(Tag)
        .select_from(task_tags_table)
        .join(Tag, Tag.id == task_tags_table.c.tag_id)
        .where(task_tags_table.c.task_id == task_id)
    )
    result = await db.execute(query)
    return result.scalars().all()
