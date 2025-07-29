from fastapi import APIRouter, Depends, status
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from services import task as task_service
from services.auth_handler import get_current_user
from core.db.async_session import get_db_session
from models.schemas.task import TaskCreate, TaskUpdate, TaskInDB

router = APIRouter(prefix="/api", tags=["Tasks"])


@router.get("/projects/{project_id}/tasks")
async def list_tasks(
    project_id: str,
    status: Optional[str] = None,
    assignee: Optional[UUID] = None,
    search: Optional[str] = "",
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await task_service.list_tasks(db, project_id, status, assignee, search)


@router.post("/projects/{project_id}/tasks", response_model=TaskInDB)
async def create_task(
    project_id: str,
    task: TaskCreate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await task_service.create_task(db, task)


@router.get("/tasks/{task_id}", response_model=TaskInDB)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await task_service.get_task(db, task_id)


@router.put("/tasks/{task_id}", response_model=TaskInDB)
async def update_task(
    task_id: str,
    task: TaskUpdate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await task_service.update_task(db, task_id, task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    await task_service.delete_task(db, task_id)


@router.post("/tasks/{task_id}/duplicate", response_model=TaskInDB)
async def duplicate_task(
    task_id: str,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await task_service.duplicate_task(db, task_id)


@router.get("/tasks/{task_id}/subtasks")
async def list_subtasks(
    task_id: str,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await task_service.list_subtasks(db, task_id)


@router.post("/tasks/{task_id}/subtasks")
async def add_subtask(
    task_id: str,
    subtask: TaskCreate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await task_service.add_subtask(db, task_id, subtask)


@router.delete("/tasks/{task_id}/subtasks/{subtask_id}")
async def delete_subtask(
    task_id: str,
    subtask_id: str,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await task_service.remove_subtask(db, task_id, subtask_id)
