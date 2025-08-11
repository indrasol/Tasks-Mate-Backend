from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas.task_attachment import TaskAttachmentCreate, TaskAttachmentUpdate, TaskAttachmentInDB
from app.services.task_attachment_service import create_task_attachment, get_task_attachment, update_task_attachment, delete_task_attachment
from app.services.auth_handler import verify_token
from app.services.rbac import get_project_role

router = APIRouter()

async def project_rbac(project_id: str, user=Depends(verify_token)):
    role = await get_project_role(user["id"], project_id)
    if not role:
        raise HTTPException(status_code=403, detail="Not a member of this project")
    return role

@router.post("", response_model=TaskAttachmentInDB)
async def create_attachment(attachment: TaskAttachmentCreate, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    if role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await create_task_attachment({**attachment.dict(), "created_by": user["id"]})
    return result.data[0]

@router.get("/{attachment_id}", response_model=TaskAttachmentInDB)
async def read_attachment(attachment_id: str, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    result = await get_task_attachment(attachment_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")
    return result.data

@router.put("/{attachment_id}", response_model=TaskAttachmentInDB)
async def update_attachment(attachment_id: str, attachment: TaskAttachmentUpdate, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    if role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await update_task_attachment(attachment_id, {**attachment.dict(exclude_unset=True), "updated_by": user["id"]})
    return result.data[0]

@router.delete("/{attachment_id}")
async def delete_attachment(attachment_id: str, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    if role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can delete attachment")
    await delete_task_attachment(attachment_id, {"deleted_by": user["id"]})
    return {"ok": True}