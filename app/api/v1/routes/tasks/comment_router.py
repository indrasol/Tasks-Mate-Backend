from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from app.models.schemas.task_comment import TaskCommentCreate, TaskCommentUpdate, TaskCommentInDB
from app.services.task_comment_service import create_task_comment, get_task_comment, update_task_comment, delete_task_comment, get_comments_for_task
from app.services.auth_handler import verify_token
from app.services.rbac import get_project_role

router = APIRouter()

class ReplyCreate(BaseModel):
    content: str
    parent_comment_id: str

async def project_rbac(project_id: str, user=Depends(verify_token)):
    role = await get_project_role(user["id"], project_id)
    if not role:
        raise HTTPException(status_code=403, detail="Not a member of this project")
    return role


@router.post("/", response_model=TaskCommentInDB, status_code=status.HTTP_201_CREATED)
async def create_comment(comment: TaskCommentCreate, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    """Create a new top-level comment on a task."""
    payload = {**comment.dict()}
    # Ensure content is provided
    # if not payload.get("content") and not payload.get("comment"):
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Comment content is required"
    #     )
        
    # Ensure content mirrors legacy column if needed
    if payload.get("content") and not payload.get("comment"):
        payload["comment"] = payload["content"]
        
    # Stamp creator
    payload["created_by"] = user.get("username") or user.get("email") or user.get("id")
    
    try:
        result = await create_task_comment(payload)
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create comment"
            )
        return result.data[0]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/reply", response_model=TaskCommentInDB, status_code=status.HTTP_201_CREATED)
async def reply_to_comment(reply: ReplyCreate, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    """Reply to an existing comment."""
    # Get the parent comment to ensure it exists and get task_id
    parent = await get_task_comment(reply.parent_comment_id)
    if not parent.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent comment not found"
        )
    
    payload = {
        "task_id": parent.data.get("task_id"),
        "content": reply.content,
        "parent_comment_id": reply.parent_comment_id,
        "created_by": user.get("username") or user.get("email") or user.get("id")
    }
    
    try:
        result = await create_task_comment(payload)
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create reply"
            )
        return result.data[0]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("", response_model=List[TaskCommentInDB])
async def list_task_comments(
    task_id: str = Query(..., description="ID of the task to get comments for"),
    search: Optional[str] = Query(None, description="Search term to filter comments"),
    limit: int = Query(20, ge=1, le=100, description="Number of comments to return"),
    offset: int = Query(0, ge=0, description="Number of comments to skip"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("asc", description="Sort order (asc or desc)"),
    user=Depends(verify_token)
):
    """
    Get all comments for a task, including nested replies.
    
    Returns a tree structure where each comment may have a 'replies' array
    containing its direct replies.
    """
    try:
        # Note: The service layer now handles the tree structure
        comments = await get_comments_for_task(
            task_id,
            search=search,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return comments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch comments: {str(e)}"
        )

@router.get("/{comment_id}", response_model=TaskCommentInDB)
async def read_comment(comment_id: str, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    result = await get_task_comment(comment_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")
    return result.data

@router.put("/{comment_id}", response_model=TaskCommentInDB)
async def update_comment(comment_id: str, comment: TaskCommentUpdate, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    # Owners/Admins can edit any comment; others can only edit their own
    if role not in ["owner", "admin"]:
        existing = await get_task_comment(comment_id)
        if not existing or not existing.data:
            raise HTTPException(status_code=404, detail="Not found")
        created_by = str(existing.data.get("created_by") or "").lower()
        user_identifiers = {str(user.get("id") or "").lower(), str(user.get("username") or "").lower(), str(user.get("email") or "").lower()}
        if created_by not in user_identifiers:
            raise HTTPException(status_code=403, detail="Not authorized")
    payload = comment.dict(exclude_unset=True)
    # Keep legacy column in sync if `content` provided
    if payload.get("content"):
        payload.setdefault("comment", payload["content"]) 
    result = await update_task_comment(comment_id, payload)
    return result.data[0]

@router.delete("/{comment_id}")
async def delete_comment(comment_id: str, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    # Owners/Admins can delete any comment; creators can delete their own
    if role not in ["owner", "admin"]:
        existing = await get_task_comment(comment_id)
        if not existing or not existing.data:
            raise HTTPException(status_code=404, detail="Not found")
        created_by = str(existing.data.get("created_by") or "").lower()
        user_identifiers = {str(user.get("id") or "").lower(), str(user.get("username") or "").lower(), str(user.get("email") or "").lower()}
        if created_by not in user_identifiers:
            raise HTTPException(status_code=403, detail="Only owner/admin or comment author can delete")
    await delete_task_comment(comment_id, {"deleted_by": user["id"]})
    return {"ok": True}