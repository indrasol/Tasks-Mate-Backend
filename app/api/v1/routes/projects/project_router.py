from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.api.v1.routes.organizations.org_rbac import org_rbac
from app.api.v1.routes.projects.proj_rbac import project_rbac
from app.models.enums import RoleEnum
from app.models.schemas.project import ProjectCard, ProjectCreate, ProjectUpdate, ProjectInDB
from app.services.project_service import create_project, get_project, update_project, delete_project, get_projects_for_user
from app.services.auth_handler import verify_token
from app.services.rbac import get_project_role
from app.services.project_member_service import create_project_member
from app.services.role_service import create_role, get_role_by_name
from app.services.utils import inject_audit_fields

router = APIRouter()



@router.post("/", response_model=ProjectInDB)
async def create_project_route(project: ProjectCreate, user=Depends(verify_token), org_role=Depends(org_rbac)):
    # Only global admin/editor can create projects
    if org_role not in [RoleEnum.OWNER.value, RoleEnum.ADMIN.value]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    data = inject_audit_fields(project.dict(), user["id"], action="create_proj")
        
    result = await create_project(data)
    project_id = result.data[0]["project_id"]

    result_role = await get_role_by_name(RoleEnum.OWNER.value)
    if result_role.data and len(result_role.data) > 0:
        role_id = result_role.data[0]["role_id"]
    else:
        result_role = await create_role({"name":RoleEnum.OWNER.value})
        if result_role.data:
            role_id = result_role.data[0]["role_id"]


    await create_project_member({
        "user_id": user["id"],
        "project_id": str(project_id),
        "role": str(role_id),
        "is_active": True,
        "created_by": user["id"]
    })
    return result.data[0]

@router.get("/", response_model=List[ProjectCard])
async def list_user_projects(org_id: str, user=Depends(verify_token), org_role=Depends(org_rbac)):
    """
    List all projects where the current user is a member.
    """
    return await get_projects_for_user(user["id"], org_id)

@router.get("/{project_id}", response_model=ProjectInDB)
async def read_project(project_id: str, user=Depends(verify_token), proj_role=Depends(project_rbac)):
    if not proj_role:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await get_project(project_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")
    return result.data

@router.put("/{project_id}", response_model=ProjectInDB)
async def update_project_route(project_id: str, project: ProjectUpdate, user=Depends(verify_token), proj_role=Depends(project_rbac)):
    if proj_role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await update_project(project_id, {**project.dict(exclude_unset=True), "updated_by": user["id"]})
    return result.data[0]

@router.delete("/{project_id}")
async def delete_project_route(project_id: str, user=Depends(verify_token), proj_role=Depends(project_rbac)):
    if proj_role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can delete project")
    await delete_project(project_id, {"deleted_by": user["id"]})
    return {"ok": True}