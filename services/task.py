from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from models.db_schemas.db_schema_models import Task
from models.schemas.task import TaskCreate, TaskUpdate
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


async def list_tasks(db: AsyncSession, project_id: str, status=None, assignee=None, search=""):
    query = select(Task).where(Task.project_id == project_id)
    if status:
        query = query.where(Task.status == status)
    if assignee:
        query = query.where(Task.assignee_id == assignee)
    if search:
        query = query.where(Task.title.ilike(f"%{search}%"))
    try:
        result = await db.execute(query)
        return result.scalars().all()
    except Exception:
        logger.exception("Failed to list tasks")
        raise HTTPException(status_code=500, detail="Could not fetch tasks")


async def create_task(db: AsyncSession, task_data: TaskCreate):
    task = Task(**task_data.dict())
    db.add(task)
    try:
        await db.commit()
        await db.refresh(task)
        return task
    except Exception:
        await db.rollback()
        logger.exception("Failed to create task")
        raise HTTPException(status_code=500, detail="Could not create task")


async def get_task(db: AsyncSession, task_id: str):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


async def update_task(db: AsyncSession, task_id: str, update: TaskUpdate):
    task = await get_task(db, task_id)
    for k, v in update.dict(exclude_unset=True).items():
        setattr(task, k, v)
    try:
        await db.commit()
        await db.refresh(task)
        return task
    except Exception:
        await db.rollback()
        logger.exception("Failed to update task")
        raise HTTPException(status_code=500, detail="Could not update task")


async def delete_task(db: AsyncSession, task_id: str):
    task = await get_task(db, task_id)
    try:
        await db.delete(task)
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception("Failed to delete task")
        raise HTTPException(status_code=500, detail="Could not delete task")


async def duplicate_task(db: AsyncSession, task_id: str):
    task = await get_task(db, task_id)
    copy_id = f"{task.task_id}_copy"
    copy = Task(
        task_id=copy_id,
        project_id=task.project_id,
        title=f"{task.title} (Copy)",
        description=task.description,
        assignee_id=task.assignee_id,
        due_date=task.due_date,
        tags=task.tags,
        priority=task.priority
    )
    db.add(copy)
    await db.commit()
    await db.refresh(copy)
    return copy


# ✅ Subtasks as embedded IDs
async def list_subtasks(db: AsyncSession, parent_id: str):
    parent = await get_task(db, parent_id)
    if not parent.sub_tasks:
        return []
    result = await db.execute(select(Task).where(Task.task_id.in_(parent.sub_tasks)))
    return result.scalars().all()


async def add_subtask(db: AsyncSession, parent_id: str, subtask_data: TaskCreate):
    subtask = Task(**subtask_data.dict())
    db.add(subtask)
    await db.commit()
    await db.refresh(subtask)

    parent = await get_task(db, parent_id)
    parent.sub_tasks.append(subtask.task_id)
    await db.commit()
    return subtask


async def remove_subtask(db: AsyncSession, parent_id: str, subtask_id: str):
    # Delete the subtask
    subtask = await get_task(db, subtask_id)
    await db.delete(subtask)

    # Remove reference from parent
    parent = await get_task(db, parent_id)
    if subtask_id in parent.sub_tasks:
        parent.sub_tasks.remove(subtask_id)
    await db.commit()
