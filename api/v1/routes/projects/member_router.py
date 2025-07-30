from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from models.schemas.project_member import ProjectMemberCreate, ProjectMemberUpdate, ProjectMemberInDB
from services.project_member_service import create_project_member, get_project_member, update_project_member, delete_project_member, get_members_for_project
from services.auth_handler import verify_token
from services.rbac import get_project_role

router = APIRouter()

async def project_rbac(project_id: str, user=Depends(verify_token)):
    role = await get_project_role(user["id"], project_id)
    if not role:
        raise HTTPException(status_code=403, detail="Not a member of this project")
    return role

@router.post("/", response_model=ProjectMemberInDB)
async def create_member(member: ProjectMemberCreate, user=Depends(verify_token), role=Depends(project_rbac)):
    if role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await create_project_member({**member.dict(), "created_by": user["id"]})
    return result.data[0]

@router.get("/", response_model=List[ProjectMemberInDB])
async def list_project_members(
    project_id: str = Query(...),
    search: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("user_name"),
    sort_order: str = Query("asc"),
    role: Optional[str] = Query(None),
    user=Depends(verify_token)
):
    role_check = await get_project_role(user["id"], project_id)
    if not role_check:
        raise HTTPException(status_code=403, detail="Not a member of this project")
    return await get_members_for_project(project_id, search=search, limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order, role=role)

@router.get("/{user_id}/{project_id}", response_model=ProjectMemberInDB)
async def read_member(user_id: str, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    result = await get_project_member(user_id, project_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")
    return result.data

@router.put("/{user_id}/{project_id}", response_model=ProjectMemberInDB)
async def update_member(user_id: str, project_id: str, member: ProjectMemberUpdate, user=Depends(verify_token), role=Depends(project_rbac)):
    if member.role == "owner" and role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can assign owner role")
    if member.role == "admin" and role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only owner/admin can assign admin role")
    result = await update_project_member(user_id, project_id, {**member.dict(exclude_unset=True), "updated_by": user["id"]})
    return result.data[0]

@router.delete("/{user_id}/{project_id}")
async def delete_member(user_id: str, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    if role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can remove members")
    await delete_project_member(user_id, project_id, {"deleted_by": user["id"]})
    return {"ok": True}