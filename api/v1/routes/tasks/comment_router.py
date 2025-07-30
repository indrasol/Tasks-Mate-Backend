from fastapi import APIRouter, Depends, HTTPException
from models.schemas.task_comment import TaskCommentCreate, TaskCommentUpdate, TaskCommentInDB
from services.task_comment_service import create_task_comment, get_task_comment, update_task_comment, delete_task_comment
from services.auth_handler import verify_token
from services.rbac import get_project_role

router = APIRouter()

async def project_rbac(project_id: str, user=Depends(verify_token)):
    role = await get_project_role(user["id"], project_id)
    if not role:
        raise HTTPException(status_code=403, detail="Not a member of this project")
    return role

@router.post("/", response_model=TaskCommentInDB)
async def create_comment(comment: TaskCommentCreate, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    if role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await create_task_comment({**comment.dict(), "created_by": user["id"]})
    return result.data[0]

@router.get("/{comment_id}", response_model=TaskCommentInDB)
async def read_comment(comment_id: str, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    result = await get_task_comment(comment_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")
    return result.data

@router.put("/{comment_id}", response_model=TaskCommentInDB)
async def update_comment(comment_id: str, comment: TaskCommentUpdate, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    if role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await update_task_comment(comment_id, {**comment.dict(exclude_unset=True), "updated_by": user["id"]})
    return result.data[0]

@router.delete("/{comment_id}")
async def delete_comment(comment_id: str, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    if role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can delete comment")
    await delete_task_comment(comment_id, {"deleted_by": user["id"]})
    return {"ok": True}