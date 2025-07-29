# api/v1/routes/organizations/routes.py

from fastapi import APIRouter, Depends, Query, status
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from services.organization import (
    get_organizations,
    create_organization,
    get_organization_by_id,
    update_organization,
    delete_organization
)
from models.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationInDB
)
from core.db.async_session import get_db_session
from services.auth_handler import get_current_user

router = APIRouter(prefix="/api/organizations", tags=["Organizations"])


@router.get("/", response_model=dict)
async def list_organizations(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = "",
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    skip = (page - 1) * limit
    return await get_organizations(db, skip=skip, limit=limit, search=search)


@router.post("/", response_model=OrganizationInDB, status_code=status.HTTP_201_CREATED)
async def create(
    org: OrganizationCreate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await create_organization(db, org, UUID(user["sub"]))


@router.get("/{org_id}", response_model=OrganizationInDB)
async def retrieve(
    org_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await get_organization_by_id(db, org_id)


@router.put("/{org_id}", response_model=OrganizationInDB)
async def update(
    org_id: UUID,
    update_data: OrganizationUpdate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    return await update_organization(db, org_id, update_data)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    org_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    await delete_organization(db, org_id)
