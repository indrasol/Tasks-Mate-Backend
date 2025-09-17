from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from app.services.auth_handler import verify_token
from app.services.bug_service import get_bug_dependencies
from app.services.task_service import create_tracker_task, delete_tracker_task
from app.models.schemas.tracker_task import TrackerTaskCreate, TrackerTaskInDB

router = APIRouter(prefix="/dependencies", tags=["bug_dependencies"])

@router.get("", response_model=List[Dict[str, Any]])
async def list_bug_dependencies(
    bug_id: str,
    current_user: dict = Depends(verify_token)
):
    """List all dependencies for a bug."""
    try:
        dependencies = await get_bug_dependencies(bug_id)
        return dependencies
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("", response_model=TrackerTaskInDB)
async def create_bug_dependency_route(bug_id: str, task: TrackerTaskCreate, user=Depends(verify_token)):
    result = await create_tracker_task({**task.dict(), "created_by": user["username"], "bug_id": bug_id}, user["username"])
    return result.data[0]

@router.delete("/{task_id}", response_model=TrackerTaskInDB)
async def delete_bug_dependency_route(bug_id: str, task_id: str, user=Depends(verify_token)):
    result = await delete_tracker_task(task_id, bug_id, user["username"])
    return result.data[0]
