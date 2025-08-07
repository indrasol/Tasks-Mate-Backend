from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.schemas.project_resource import ProjectResourceCreate, ProjectResourceUpdate, ProjectResourceInDB
from app.services.project_resource_service import create_project_resource, get_project_resource, update_project_resource, delete_project_resource, get_resources_for_project
from app.services.auth_handler import verify_token
from app.services.rbac import get_project_role

router = APIRouter()

async def project_rbac(project_id: str, user=Depends(verify_token)):
    role = await get_project_role(user["id"], project_id)
    if not role:
        raise HTTPException(status_code=403, detail="Not a member of this project")
    return role

@router.post("/", response_model=ProjectResourceInDB)
async def create_resource(resource: ProjectResourceCreate, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    if role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await create_project_resource({**resource.dict(), "created_by": user["username"]})
    return result.data[0]

@router.get("/", response_model=List[ProjectResourceInDB])
async def list_project_resources(
    project_id: str = Query(...),
    search: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("resource_type"),
    sort_order: str = Query("asc"),
    resource_type: Optional[str] = Query(None),
    user=Depends(verify_token)
):
    role = await get_project_role(user["id"], project_id)
    if not role:
        raise HTTPException(status_code=403, detail="Not a member of this project")
    return await get_resources_for_project(project_id, search=search, limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order, resource_type=resource_type)

@router.get("/{resource_id}", response_model=ProjectResourceInDB)
async def read_resource(resource_id: str, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    result = await get_project_resource(resource_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")
    return result.data

@router.put("/{resource_id}", response_model=ProjectResourceInDB)
async def update_resource(resource_id: str, resource: ProjectResourceUpdate, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    if role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await update_project_resource(resource_id, {**resource.dict(exclude_unset=True), "updated_by": user["id"]})
    return result.data[0]

@router.delete("/{resource_id}")
async def delete_resource(resource_id: str, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    if role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can delete resource")
    await delete_project_resource(resource_id, {"deleted_by": user["id"]})
    return {"ok": True}