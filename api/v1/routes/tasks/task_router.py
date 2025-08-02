from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from api.v1.routes.projects.proj_rbac import project_rbac
from models.schemas.task import TaskCreate, TaskUpdate, TaskInDB
from services.task_service import create_task, get_task, update_task, delete_task, get_all_tasks, get_tasks_for_project
from services.auth_handler import verify_token
from services.rbac import get_project_role

router = APIRouter()

# async def project_rbac(task_id: str, user=Depends(verify_token)):
#     # You may need to fetch project_id from the task if not provided directly
#     # For now, assume project_id is passed as a query param or path param
#     # This is a placeholder for correct project_id resolution
#     # You may want to refactor to fetch project_id from the DB using task_id
#     return await get_project_role(user["id"], task_id)

@router.post("/", response_model=TaskInDB)
async def create_task_route(task: TaskCreate, user=Depends(verify_token), role=Depends(project_rbac)):
    if role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await create_task({**task.dict(), "created_by": user["id"]})
    return result.data[0]

@router.get("/", response_model=List[TaskInDB])
async def list_all_tasks(
    user=Depends(verify_token),
    project_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("title"),
    sort_order: str = Query("asc"),
    status: Optional[str] = Query(None)
):
    if project_id:
        role = await get_project_role(user["id"], project_id)
        if not role:
            raise HTTPException(status_code=403, detail="Not a member of this project")
        return await get_tasks_for_project(project_id, search=search, limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order, status=status)
    return await get_all_tasks(search=search, limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order, status=status)

@router.get("/{task_id}", response_model=TaskInDB)
async def read_task(task_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    result = await get_task(task_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")
    return result.data

@router.put("/{task_id}", response_model=TaskInDB)
async def update_task_route(task_id: str, task: TaskUpdate, user=Depends(verify_token), role=Depends(project_rbac)):
    if role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await update_task(task_id, {**task.dict(exclude_unset=True), "updated_by": user["id"]})
    return result.data[0]

@router.delete("/{task_id}")
async def delete_task_route(task_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    if role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can delete task")
    await delete_task(task_id, {"deleted_by": user["id"]})
    return {"ok": True}