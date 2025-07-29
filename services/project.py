from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from typing import List
from uuid import UUID
import logging

from models.db_schemas.db_schema_models import Project
from models.schemas.project import ProjectCreate, ProjectUpdate

logger = logging.getLogger(__name__)


async def get_projects(db: AsyncSession, skip=0, limit=10, search="", org_id: UUID = None):
    try:
        query = select(Project).where(Project.is_active == True)
        if org_id:
            query = query.where(Project.org_id == org_id)
        if search:
            query = query.where(Project.name.ilike(f"%{search}%"))

        result = await db.execute(query.offset(skip).limit(limit))
        projects = result.scalars().all()

        total = await db.scalar(select(func.count()).select_from(Project).where(Project.is_active == True))
        return {
            "projects": projects,
            "total": total,
            "page": skip // limit + 1,
            "limit": limit
        }
    except SQLAlchemyError:
        logger.exception("Failed to fetch projects")
        raise HTTPException(status_code=500, detail="Could not fetch projects")


async def create_project(db: AsyncSession, project_data: ProjectCreate, user_id: UUID):
    try:
        project = Project(**project_data.dict(), created_by=user_id)
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project
    except SQLAlchemyError:
        logger.exception("Failed to create project")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Could not create project")


async def get_project(db: AsyncSession, project_id: str):
    project = await db.get(Project, project_id)
    if not project or not project.is_active:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def update_project(db: AsyncSession, project_id: str, update_data: ProjectUpdate):
    project = await get_project(db, project_id)
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(project, field, value)
    try:
        await db.commit()
        await db.refresh(project)
        return project
    except SQLAlchemyError:
        logger.exception("Failed to update project")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Could not update project")


async def delete_project(db: AsyncSession, project_id: str):
    project = await get_project(db, project_id)
    project.is_active = False
    try:
        await db.commit()
    except SQLAlchemyError:
        logger.exception("Failed to delete project")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Could not delete project")


async def archive_project(db: AsyncSession, project_id: str):
    project = await get_project(db, project_id)
    project.status = "archived"
    await db.commit()
    return {"archived": True}


async def restore_project(db: AsyncSession, project_id: str):
    project = await get_project(db, project_id)
    project.status = "not_started"
    await db.commit()
    return {"archived": False}
