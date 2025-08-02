
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.api.v1.routes.organizations.org_rbac import org_rbac
from app.models.enums import DesignationEnum, RoleEnum
from app.models.schemas.organization import OrganizationCreate, OrganizationUpdate, OrganizationInDB
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

@router.post("/", response_model=OrganizationInDB)
async def create_org(org: OrganizationCreate, user=Depends(verify_token)):
    # Only global admin/editor can create orgs
    # if user.get("role") not in ["admin", "editor"]:
    #     raise HTTPException(status_code=403, detail="Not authorized")
    result_org = await create_organization({**org.dict(), "created_by": user["id"]})
    org_id = result_org.data[0]["org_id"]

    result_role = await get_role_by_name(RoleEnum.OWNER.value)
    if result_role.data and len(result_role.data) > 0:
        role_id = result_role.data["role_id"]
    else:
        result_role = await create_role({"name":RoleEnum.OWNER.value})
        if result_role.data:
            role_id = result_role.data[0]["role_id"]
    
    await create_organization_member({
        "user_id": user["id"],
        "org_id": org_id,
        # "designation": DesignationEnum.MANAGER,
        "role": role_id,
        # "is_active": True,
        "invited_by": user["id"],
        # "invited_at": datetime.now(),
        # "accepted_at": datetime.now()
    })
    return result_org.data[0]

@router.get("/", response_model=List[OrganizationInDB])
async def list_user_organizations(user=Depends(verify_token)):
    """
    List all organizations the user is a member of or invited to.
    """
    return await get_organizations_for_user(user["id"], user.get("email"))

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
    result = await update_organization(org_id, {**org.dict(exclude_unset=True), "updated_by": user["id"]})
    return result.data[0]

@router.delete("/{org_id}")
async def delete_org(org_id: str, user=Depends(verify_token), role=Depends(org_rbac)):
    if role != RoleEnum.OWNER.value:
        raise HTTPException(status_code=403, detail="Only owner can delete organization")
    await delete_organization(org_id, {"deleted_by": user["id"]})
    return {"ok": True}