# app/api/v1/routes/tasks/attachment_router.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, UploadFile, File, Form

from app.models.schemas.task_attachment import (
    TaskAttachmentCreate, TaskAttachmentUpdate, TaskAttachmentInDB
)
from app.services.task_attachment_service import (
    create_task_attachment,
    get_task_attachment,
    update_task_attachment,
    delete_task_attachment,
    list_task_attachments,
    upload_and_create_task_attachment
)
from app.services.auth_handler import verify_token
from app.services.rbac import get_project_role
from app.services.task_service import get_task

router = APIRouter()

async def project_rbac(project_id: str, user=Depends(verify_token)):
    role = await get_project_role(user["id"], project_id)
    if not role:
        raise HTTPException(status_code=403, detail="Not a member of this project")
    return role

async def _assert_task_in_project(task_id: str, project_id: str):
    task_res = await get_task(task_id)
    task = getattr(task_res, "data", None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if str(task.get("project_id")) != str(project_id):
        raise HTTPException(status_code=403, detail="Task does not belong to this project")
    return task

@router.post("", response_model=TaskAttachmentInDB, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    task_id: str = Form(...),
    project_id: str = Form(...),  # kept for RBAC check
    title: Optional[str] = Form(None),
    is_inline: Optional[bool] = Form(None),
    file: UploadFile = File(...),
    user=Depends(verify_token),
    role=Depends(project_rbac),
):
    """
    Upload a file to storage and create an attachment row.
    Enforces per-task limit.
    """
    try:
        # make sure the task is in that project and get it for title
        task = await _assert_task_in_project(task_id, project_id)
        
        data = await upload_and_create_task_attachment(
            task_id=task_id,
            file=file,
            title=title,
            user_id=user["id"],
            username=user.get("username") or user.get("email") or user["id"],
            task_title=task.get("title") or task.get("name"),
            is_inline=is_inline
        )
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload attachment: {e}")


@router.get("/{attachment_id}", response_model=TaskAttachmentInDB)
async def read_attachment(
    attachment_id: str,
    project_id: str,
    user=Depends(verify_token),
    role=Depends(project_rbac),
):
    try:
        result = await get_task_attachment(attachment_id)
        data = result.get("data", result) if hasattr(result, "get") else result
        if not data:
            raise HTTPException(status_code=404, detail="Attachment not found")
        att = data[0] if isinstance(data, list) else data
        # Validate via owning task's project membership
        await _assert_task_in_project(att.get("task_id"), project_id)
        return att
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch attachment")


@router.put("/{attachment_id}", response_model=TaskAttachmentInDB)
async def update_attachment(
    attachment_id: str,
    attachment: TaskAttachmentUpdate,
    project_id: str,
    user=Depends(verify_token),
    role=Depends(project_rbac),
):
    try:
        current = await get_task_attachment(attachment_id)
        if not current or not getattr(current, "data", None):
            raise HTTPException(status_code=404, detail="Attachment not found")
        att = current.data[0] if isinstance(current.data, list) else current.data
        task = await _assert_task_in_project(att.get("task_id"), project_id)

        result = await update_task_attachment(
            attachment_id,
            attachment.dict(exclude_unset=True),
            user_id=user["username"],
            task_title=task.get("title") or task.get("name"),
        )
        return result.get("data", [result])[0] if hasattr(result, "get") else result
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update attachment")


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: str,
    project_id: str,
    user=Depends(verify_token),
    role=Depends(project_rbac),
):
    try:
        current = await get_task_attachment(attachment_id)
        if not current or not getattr(current, "data", None):
            raise HTTPException(status_code=404, detail="Attachment not found")
        att = current.data[0] if isinstance(current.data, list) else current.data
        task = await _assert_task_in_project(att.get("task_id"), project_id)

        # Force hard delete: remove from storage and table
        await delete_task_attachment(
            attachment_id,
            username=user["username"],
            soft_delete=False,
            task_title=task.get("title") or task.get("name"),
        )
        return None
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete attachment")


@router.get("", response_model=List[TaskAttachmentInDB])
async def list_attachments(
    task_id: str = Query(...),
    user=Depends(verify_token),
):
    try:
        result = await list_task_attachments(task_id)
        # Extract data from Supabase response
        attachments = result.data if hasattr(result, 'data') else []
        return attachments
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list attachments: {str(e)}")
