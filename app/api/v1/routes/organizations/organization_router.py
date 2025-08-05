
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException
from app.api.v1.routes.organizations.org_rbac import org_rbac
from app.models.enums import DesignationEnum, RoleEnum
from app.models.schemas.organization import OrganizationCreate, OrganizationDelete, OrganizationUpdate, OrganizationInDB, OrgCard
from app.services.organization_service import create_organization, get_organization, update_organization, delete_organization, get_organizations_for_user
from app.services.auth_handler import verify_token
from app.services.rbac import get_org_role
from app.services.organization_member_service import create_organization_member
from app.services.role_service import create_role, get_role_by_name

router = APIRouter()

# async def org_rbac(org_id: str, user=Depends(verify_token)):
#     role = await get_org_role(user["id"], org_id)
#     if not role:
#         raise HTTPException(status_code=403, detail="Not a member of this organization")
#     return role

@router.post("/", response_model=OrgCard)
async def create_org(org: OrganizationCreate, user=Depends(verify_token)):
    # Only global admin/editor can create orgs
    # if user.get("role") not in ["admin", "editor"]:
    #     raise HTTPException(status_code=403, detail="Not authorized")
    # Prepare data, exclude None values so we don't send columns that may not exist
    org_data = org.model_dump(exclude_none=True)
    # Ensure enum types are serialized properly (e.g., RoleEnum -> 'owner')
    # if isinstance(org_data.get("role"), RoleEnum):
    #     role = org_data["role"].value
    
    name = org_data.get("name")
    description = org_data.get("description")
    designation = org_data.get("designation")
    username = user["username"]

    try:
        result_org = await create_organization({"name":name, "description":description, "designation":designation, "created_by": username})
        org_id = result_org.data[0]["org_id"]
        role = org_data.get("role", RoleEnum.OWNER.value)
        
        await create_organization_member({
            "user_id": user["id"],
            "org_id": org_id,
            "designation": designation,
            "role": role,
            "invited_by": user["username"],
        })
        
        # Return simplified OrgCard response
        return OrgCard(
            org_id=org_id,
            name=name,
            description=description,
            role=role,
            designation=designation,
            project_count=0,  # New org starts with 0 projects
            member_count=1,   # New org starts with 1 member (creator)
            created_by=username,
            created_at=datetime.now()
        )
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(
                status_code=409,  # Conflict - appropriate for duplicate resources
                detail=f"Organization with name '{name}' already exists. Please choose a different name."
            )
        # Re-raise other ValueError exceptions
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[OrgCard])
async def list_user_organizations(user=Depends(verify_token)):
    """
    List all organizations the user is a member of or invited to.
    Returns simplified OrgCard objects with essential information.
    """
    return await get_organizations_for_user(user["id"], user["username"], user.get("email"))

@router.get("/{org_id}", response_model=OrganizationInDB)
async def read_org(org_id: str, user=Depends(verify_token), role=Depends(org_rbac)):
    result = await get_organization(org_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")
    return result.data

@router.put("/{org_id}", response_model=OrganizationInDB)
async def update_org(org_id: str, org: OrganizationUpdate, user=Depends(verify_token), role=Depends(org_rbac)):
    if role not in [RoleEnum.OWNER.value, RoleEnum.ADMIN.value]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await update_organization(org_id, {**org.dict(exclude_unset=True), "updated_by": user["username"]})
    return result.data[0]

@router.delete("/{org_id}")
async def delete_org(org_id: str, org:OrganizationDelete , user=Depends(verify_token), role=Depends(org_rbac)):
    if role != RoleEnum.OWNER.value:
        raise HTTPException(status_code=403, detail="Only owner can delete organization")
  
    await delete_organization(org_id, {"delete_reason": org.delete_reason, "deleted_by": user["username"]})
    return {"ok": True}