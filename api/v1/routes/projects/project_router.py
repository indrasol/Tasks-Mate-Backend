from typing import List
from fastapi import APIRouter, Depends, HTTPException
from models.schemas.project import ProjectCreate, ProjectUpdate, ProjectInDB
from services.project_service import create_project, get_project, update_project, delete_project, get_projects_for_user
from services.auth_handler import verify_token
from services.rbac import get_project_role
from services.project_member_service import create_project_member

router = APIRouter()

async def project_rbac(project_id: str, user=Depends(verify_token)):
    role = await get_project_role(user["id"], project_id)
    if not role:
        raise HTTPException(status_code=403, detail="Not a member of this project")
    return role

@router.post("/", response_model=ProjectInDB)
async def create_project_route(project: ProjectCreate, user=Depends(verify_token)):
    # Only global admin/editor can create projects
    if user.get("role") not in ["admin", "editor"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await create_project({**project.dict(), "created_by": user["id"]})
    project_id = result.data[0]["project_id"]
    await create_project_member({
        "user_id": user["id"],
        "project_id": project_id,
        "role": "owner",
        "is_active": True,
        "created_by": user["id"]
    })
    return result.data[0]

@router.get("/", response_model=List[ProjectInDB])
async def list_user_projects(user=Depends(verify_token)):
    """
    List all projects where the current user is a member.
    """
    return await get_projects_for_user(user["id"])

@router.get("/{project_id}", response_model=ProjectInDB)
async def read_project(project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    result = await get_project(project_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")
    return result.data

@router.put("/{project_id}", response_model=ProjectInDB)
async def update_project_route(project_id: str, project: ProjectUpdate, user=Depends(verify_token), role=Depends(project_rbac)):
    if role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await update_project(project_id, {**project.dict(exclude_unset=True), "updated_by": user["id"]})
    return result.data[0]

@router.delete("/{project_id}")
async def delete_project_route(project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    if role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can delete project")
    await delete_project(project_id, {"deleted_by": user["id"]})
    return {"ok": True}