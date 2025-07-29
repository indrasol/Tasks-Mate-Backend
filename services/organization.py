# services/organization_service.py

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
import logging

from models.db_schemas.db_schema_models import Organization
from models.schemas.organization import OrganizationCreate, OrganizationUpdate

logger = logging.getLogger(__name__)


async def get_organizations(db: AsyncSession, skip: int = 0, limit: int = 10, search: str = ""):
    try:
        query = select(Organization).where(Organization.is_deleted == False)
        if search:
            query = query.where(Organization.name.ilike(f"%{search}%"))
        result = await db.execute(query.offset(skip).limit(limit))
        organizations = result.scalars().all()
        total = await db.scalar(select(func.count()).select_from(Organization).where(Organization.is_deleted == False))
        return {
            "organizations": organizations,
            "total": total,
            "page": skip // limit + 1,
            "limit": limit
        }
    except SQLAlchemyError as e:
        logger.exception("Failed to fetch organizations")
        raise HTTPException(status_code=500, detail="Error fetching organizations")


async def create_organization(db: AsyncSession, org_data: OrganizationCreate, user_id: UUID):
    try:
        org = Organization(
            name=org_data.name,
            description=org_data.description,
            created_by=user_id
        )
        db.add(org)
        await db.commit()
        await db.refresh(org)
        logger.info(f"Organization created: {org.name}")
        return org
    except SQLAlchemyError as e:
        logger.exception("Failed to create organization")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error creating organization")


async def get_organization_by_id(db: AsyncSession, org_id: UUID):
    org = await db.get(Organization, org_id)
    if not org or org.is_deleted:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


async def update_organization(db: AsyncSession, org_id: UUID, update: OrganizationUpdate):
    org = await get_organization_by_id(db, org_id)
    for field, value in update.dict(exclude_unset=True).items():
        setattr(org, field, value)
    try:
        await db.commit()
        await db.refresh(org)
        return org
    except SQLAlchemyError as e:
        logger.exception(f"Failed to update organization {org_id}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error updating organization")


async def delete_organization(db: AsyncSession, org_id: UUID):
    org = await get_organization_by_id(db, org_id)
    org.is_deleted = True
    try:
        await db.commit()
    except SQLAlchemyError as e:
        logger.exception(f"Failed to delete organization {org_id}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting organization")
