from fastapi import APIRouter, Depends, HTTPException
from models.schemas.project_member import ProjectMemberCreate, ProjectMemberUpdate, ProjectMemberInDB
from services.project_member_service import create_project_member, get_project_member, update_project_member, delete_project_member
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