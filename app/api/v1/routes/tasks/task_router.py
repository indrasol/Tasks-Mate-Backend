from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
# from app.api.v1.routes.projects.proj_rbac import project_rbac
from app.models.schemas.task import TaskCreate, TaskUpdate, TaskInDB, TaskCardView
from app.services.task_service import create_task, get_task, update_task, delete_task, get_all_tasks, get_tasks_for_project, add_subtask, remove_subtask, add_dependency, remove_dependency
from app.services.auth_handler import verify_token
from app.services.rbac import get_project_role
from app.api.v1.routes.emails.email_routes import send_task_assignment_email

router = APIRouter()

# async def project_rbac(task_id: str, user=Depends(verify_token)):
#     # You may need to fetch project_id from the task if not provided directly
#     # For now, assume project_id is passed as a query param or path param
#     # This is a placeholder for correct project_id resolution
#     # You may want to refactor to fetch project_id from the DB using task_id
#     return await get_project_role(user["id"], task_id)

@router.post("", response_model=TaskInDB)
async def create_task_route(task: TaskCreate, user=Depends(verify_token)):
    # if role not in ["owner", "admin"]:
    #     raise HTTPException(status_code=403, detail="Not authorized")
    result = await create_task({**task.model_dump(), "created_by": user["username"]}, user["username"])
    await send_task_assignment_email(result.data[0])
    return result.data[0]

@router.get("", response_model=List[TaskCardView])
async def list_all_tasks(
    user=Depends(verify_token),
    org_id: Optional[str] = Query(None),
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
        return await get_tasks_for_project(project_id, search=search, limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order, status=status, org_id=org_id)
    return await get_all_tasks(search=search, limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order, status=status, org_id=org_id)

@router.get("/{task_id}", response_model=TaskInDB)
async def read_task(task_id: str, user=Depends(verify_token)):
    result = await get_task(task_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")
    return result.data

@router.put("/{task_id}", response_model=TaskInDB)
async def update_task_route(task_id: str, task: TaskUpdate, user=Depends(verify_token)):
    # if role not in ["owner", "admin"]:
    #     raise HTTPException(status_code=403, detail="Not authorized")
    result = await update_task(task_id, {**task.dict(exclude_unset=True), "updated_by": user["username"]}, user["username"])

    if task.assignee:
        await send_task_assignment_email(result.data[0])
    
    return result.data[0]

@router.delete("/{task_id}")
async def delete_task_route(task_id: str, user=Depends(verify_token)):
    # Authorization: allow project owner/admin OR task creator/assignee
    task_result = await get_task(task_id)
    if not task_result or not getattr(task_result, "data", None):
        raise HTTPException(status_code=404, detail="Not found")

    task_data = task_result.data
    project_id = task_data.get("project_id")
    allowed = False

    # Check project role if available
    try:
        if project_id:
            role = await get_project_role(user["id"], project_id)
            if role in ["owner", "admin"]:
                allowed = True
    except Exception:
        # If role check fails, continue to check ownership below
        pass

    # Check if current user created the task or is the assignee
    if (
        (task_data.get("created_by") and task_data.get("created_by") == user.get("username"))
        or (task_data.get("assignee") and task_data.get("assignee") == user.get("username"))
    ):
        allowed = True

    if not allowed:
        raise HTTPException(status_code=403, detail="Not authorized to delete this task")

    await delete_task(task_id, user["username"])
    return {"ok": True}

# ---------------------- Subtask Management ----------------------

@router.post("/{task_id}/subtasks", response_model=TaskInDB)
async def add_subtask_to_task(task_id: str, subtask_id: str = Body(..., embed=True), user=Depends(verify_token)):
    """Append a subtask to an existing task."""
    result = await add_subtask(task_id, subtask_id, user["username"])
    return result.data[0] if hasattr(result, "data") and isinstance(result.data, list) else result.data


@router.delete("/{task_id}/subtasks/{subtask_id}", response_model=TaskInDB)
async def remove_subtask_from_task(task_id: str, subtask_id: str, user=Depends(verify_token)):
    """Remove a subtask from an existing task."""
    result = await remove_subtask(task_id, subtask_id, user["username"])
    return result.data[0] if hasattr(result, "data") and isinstance(result.data, list) else result.data


# ---------------------- Dependency Management ----------------------

@router.post("/{task_id}/dependencies", response_model=TaskInDB)
async def add_dependency_to_task(
    task_id: str,
    dependency_id: str = Body(..., embed=True),
    user=Depends(verify_token)
):
    """Append a dependency to an existing task."""
    result = await add_dependency(task_id, dependency_id, user["username"])
    return result.data[0] if hasattr(result, "data") and isinstance(result.data, list) else result.data


@router.delete("/{task_id}/dependencies/{dependency_id}", response_model=TaskInDB)
async def remove_dependency_from_task(
    task_id: str,
    dependency_id: str,
    user=Depends(verify_token)
):
    """Remove a dependency from an existing task."""
    result = await remove_dependency(task_id, dependency_id, user["username"])
    return result.data[0] if hasattr(result, "data") and isinstance(result.data, list) else result.data