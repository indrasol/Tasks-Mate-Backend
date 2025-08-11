from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas.designation import DesignationCreate, DesignationUpdate, DesignationInDB
from app.services.designation_service import (
    create_designation,
    get_designation,
    get_designations,
    update_designation,
    delete_designation,
)
from app.services.auth_handler import verify_token
from app.services.rbac import get_org_role

router = APIRouter()

async def org_rbac(org_id: str, user=Depends(verify_token)):
    role = await get_org_role(user["id"], org_id)
    if not role:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    return role

@router.post("", response_model=DesignationInDB)
async def create_designation_route(designation_data: DesignationCreate, user=Depends(verify_token)):
    result = await create_designation(designation_data.model_dump())
    return result.data[0]

@router.get("", response_model=List[DesignationInDB])
async def list_designations(
    org_id: str | None = None,
    user=Depends(verify_token)
):
    """Return global designations if `org_id` is not supplied; otherwise return org-specific ones."""
    result = await get_designations(org_id)
    return result.data

@router.get("/{designation_id}", response_model=DesignationInDB)
async def read_designation(
    designation_id: str,
    org_id: str,
    user=Depends(verify_token)
):
    result = await get_designation(designation_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")
    return result.data

@router.put("/{designation_id}", response_model=DesignationInDB)
async def update_designation_route(
    designation_id: str,
    designation: DesignationUpdate,
    org_id: str,
    user=Depends(verify_token)
):
    # if role not in ["admin", "editor"]:
    #     raise HTTPException(status_code=403, detail="Not authorized")
    result = await update_designation(designation_id, designation.dict(exclude_unset=True))
    return result.data[0]

@router.delete("/{designation_id}")
async def delete_designation_route(
    designation_id: str,
    org_id: str,
    user=Depends(verify_token)
):
    # if role != "admin":
    #     raise HTTPException(status_code=403, detail="Not authorized")
    await delete_designation(designation_id)
    return {"ok": True}
