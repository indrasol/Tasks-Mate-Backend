from fastapi import APIRouter, Depends, HTTPException
from models.schemas.task_history import TaskHistoryCreate, TaskHistoryUpdate, TaskHistoryInDB
from services.task_history_service import create_task_history, get_task_history, update_task_history, delete_task_history
from services.auth_handler import verify_token
from services.rbac import get_project_role

router = APIRouter()

async def project_rbac(project_id: str, user=Depends(verify_token)):
    role = await get_project_role(user["id"], project_id)
    if not role:
        raise HTTPException(status_code=403, detail="Not a member of this project")
    return role

@router.post("/", response_model=TaskHistoryInDB)
async def create_history(history: TaskHistoryCreate, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    if role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await create_task_history({**history.dict(), "created_by": user["id"]})
    return result.data[0]

@router.get("/{history_id}", response_model=TaskHistoryInDB)
async def read_history(history_id: str, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    result = await get_task_history(history_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")
    return result.data

@router.put("/{history_id}", response_model=TaskHistoryInDB)
async def update_history(history_id: str, history: TaskHistoryUpdate, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    if role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await update_task_history(history_id, {**history.dict(exclude_unset=True), "updated_by": user["id"]})
    return result.data[0]

@router.delete("/{history_id}")
async def delete_history(history_id: str, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    if role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can delete history")
    await delete_task_history(history_id, {"deleted_by": user["id"]})
    return {"ok": True}