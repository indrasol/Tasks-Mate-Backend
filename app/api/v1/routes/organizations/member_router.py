from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from app.api.v1.routes.organizations.org_rbac import org_rbac
from app.models.schemas.organization_member import OrganizationMemberCreate, OrganizationMemberUpdate, OrganizationMemberInDB
from app.services.organization_member_service import create_organization_member, get_organization_member, update_organization_member, delete_organization_member, get_members_for_org
from app.services.auth_handler import verify_token
from app.services.rbac import get_org_role

router = APIRouter()

# async def org_rbac(org_id: str, user=Depends(verify_token)):
#     role = await get_org_role(user["id"], org_id)
#     if not role:
#         raise HTTPException(status_code=403, detail="Not a member of this organization")
#     return role

@router.post("", response_model=OrganizationMemberInDB)
async def create_member(member: OrganizationMemberCreate, user=Depends(verify_token), role=Depends(org_rbac)):
    if role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await create_organization_member({**member.dict(), "created_by": user["username"]})
    return result.data[0]

@router.get("/{org_id}", response_model=List[OrganizationMemberInDB])
async def list_org_members(
    org_id: str,
    search: Optional[str] = Query(None),
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("updated_at"),
    sort_order: str = Query("asc"),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    user=Depends(verify_token)
):
    
    role_check = await get_org_role(user["id"], org_id)
    if not role_check:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    return await get_members_for_org(org_id, search=search, limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order, role=role, is_active=is_active)

@router.get("/{user_id}/{org_id}", response_model=OrganizationMemberInDB)
async def read_member(user_id: str, org_id: str, user=Depends(verify_token), role=Depends(org_rbac)):
    result = await get_organization_member(user_id, org_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")
    return result.data

@router.put("/{user_id}/{org_id}", response_model=OrganizationMemberInDB)
async def update_member(user_id: str, org_id: str, member: OrganizationMemberUpdate, user=Depends(verify_token), role=Depends(org_rbac)):
    if member.role == "owner" and role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can assign owner role")
    if member.role == "admin" and role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only owner/admin can assign admin role")
    result = await update_organization_member(user_id, org_id, {**member.dict(exclude_unset=True), "updated_by": user["username"]})
    return result.data[0]

@router.delete("/{user_id}/{org_id}")
async def delete_member(user_id: str, org_id: str, user=Depends(verify_token), role=Depends(org_rbac)):
    if role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can remove members")
    await delete_organization_member(user_id, org_id, {"deleted_by": user["username"]})
    return {"ok": True}