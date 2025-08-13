from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.schemas.task_history import TaskHistoryInDB
from app.services.task_history_service import  get_task_history
from app.services.auth_handler import verify_token
from app.services.rbac import get_project_role
from app.services.task_history_service import create_task_history
from app.models.schemas.task_history import TaskHistoryCreate, TaskHistoryUpdate

router = APIRouter()

# Align with POST path (no trailing slash) so GET /task-history works
@router.get("", response_model=List[TaskHistoryInDB], status_code=200)
async def read_history(
    task_id: str = Query(..., description="ID of the task to get history for"),
    title: str | None = Query(None, description="Optional task title to disambiguate sequential reuse of task_id"),
    user=Depends(verify_token)
):
    return await get_task_history(task_id, title)

# async def project_rbac(project_id: str, user=Depends(verify_token)):
#     role = await get_project_role(user["id"], project_id)
#     if not role:
#         raise HTTPException(status_code=403, detail="Not a member of this project")
#     return role

# @router.post("/", response_model=TaskHistoryInDB)
# async def create_history(history: TaskHistoryCreate, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
#     if role not in ["owner", "admin"]:
#         raise HTTPException(status_code=403, detail="Not authorized")
#     result = await create_task_history({**history.dict(), "created_by": user["id"]})
#     return result.data[0]

# @router.get("/{history_id}", response_model=TaskHistoryInDB)
# async def read_history(history_id: str, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
#     result = await get_task_history(history_id)
#     if not result.data:
#         raise HTTPException(status_code=404, detail="Not found")
#     return result.data

# @router.put("/{history_id}", response_model=TaskHistoryInDB)
# async def update_history(history_id: str, history: TaskHistoryUpdate, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
#     if role not in ["owner", "admin"]:
#         raise HTTPException(status_code=403, detail="Not authorized")
#     result = await update_task_history(history_id, {**history.dict(exclude_unset=True), "updated_by": user["id"]})
#     return result.data[0]

# @router.delete("/{history_id}")
# async def delete_history(history_id: str, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
#     if role != "owner":
#         raise HTTPException(status_code=403, detail="Only owner can delete history")
#     await delete_task_history(history_id, {"deleted_by": user["id"]})
#     return {"ok": True}

async def project_rbac(project_id: str, user=Depends(verify_token)):
    role = await get_project_role(user["id"], project_id)
    if not role:
        raise HTTPException(status_code=403, detail="Not a member of this project")
    return role

# @router.post("", response_model=TaskHistoryInDB)
# async def create_history(history: TaskHistoryCreate, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
#     if role not in ["owner", "admin"]:
#         raise HTTPException(status_code=403, detail="Not authorized")
#     result = await create_task_history({**history.dict(), "created_by": user["id"]})
#     return result.data[0]

@router.get("/{history_id}", response_model=TaskHistoryInDB)
async def read_history(history_id: str, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    result = await get_task_history(history_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")
    return result.data

# @router.put("/{history_id}", response_model=TaskHistoryInDB)
# async def update_history(history_id: str, history: TaskHistoryUpdate, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
#     if role not in ["owner", "admin"]:
#         raise HTTPException(status_code=403, detail="Not authorized")
#     result = await update_task_history(history_id, {**history.dict(exclude_unset=True), "updated_by": user["id"]})
#     return result.data[0]

# @router.delete("/{history_id}")
# async def delete_history(history_id: str, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
#     if role != "owner":
#         raise HTTPException(status_code=403, detail="Only owner can delete history")
#     await delete_task_history(history_id, {"deleted_by": user["id"]})
#     return {"ok": True}
