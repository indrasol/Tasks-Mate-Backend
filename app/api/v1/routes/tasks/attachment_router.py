from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from fastapi.params import Query
from app.models.schemas.task_attachment import TaskAttachmentCreate, TaskAttachmentUpdate, TaskAttachmentInDB
from app.services.task_attachment_service import (
    create_task_attachment, 
    get_task_attachment, 
    update_task_attachment, 
    delete_task_attachment,
    list_task_attachments
)
from app.services.auth_handler import verify_token
from app.services.rbac import get_project_role

router = APIRouter()

async def project_rbac(project_id: str, user=Depends(verify_token)):
    role = await get_project_role(user["id"], project_id)
    if not role:
        raise HTTPException(status_code=403, detail="Not a member of this project")
    return role


@router.post("/", response_model=TaskAttachmentInDB, status_code=status.HTTP_201_CREATED)
async def create_attachment(
    attachment: TaskAttachmentCreate, 
    project_id: str, 
    user=Depends(verify_token), 
    role=Depends(project_rbac)
):
    """
    Create a new task attachment with history tracking.
    
    Required roles: owner, admin
    """
    # if role not in ["owner", "admin"]:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN, 
    #         detail="Insufficient permissions to create attachments"
    #     )
    
    try:
        # Include project_id for validation and history
        attachment_data = {
            **attachment.dict(),
            "project_id": project_id,
            "created_by": user["username"]
        }
        
        # Create the attachment with user context for history
        result = await create_task_attachment(attachment_data, user_id=user["username"])
        
        # Handle response based on service return format
        attachment_data = result.get('data', [result])[0] if hasattr(result, 'get') else result
        return attachment_data
        
    except HTTPException as he:
        raise he
    except Exception as e:
        # logger.error(f"Error creating attachment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create attachment"
        )

@router.post("", response_model=TaskAttachmentInDB)
async def create_attachment(attachment: TaskAttachmentCreate, project_id: str, user=Depends(verify_token), role=Depends(project_rbac)):
    if role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await create_task_attachment({**attachment.dict(), "created_by": user["id"]})
    return result.data[0]


@router.get("/{attachment_id}", response_model=TaskAttachmentInDB)
async def read_attachment(
    attachment_id: str, 
    project_id: str, 
    user=Depends(verify_token), 
    role=Depends(project_rbac)
):
    """
    Get a task attachment by ID.
    
    Required roles: owner, admin, member, viewer
    """
    try:
        result = await get_task_attachment(attachment_id)
        
        # Handle different response formats from service
        attachment_data = result.get('data', result) if hasattr(result, 'get') else result
        
        if not attachment_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Attachment not found"
            )
            
        # Ensure the attachment belongs to the requested project
        if str(attachment_data.get('project_id')) != project_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Attachment does not belong to this project"
            )
            
        return attachment_data
        
    except HTTPException as he:
        raise he
    except Exception as e:
        # logger.error(f"Error fetching attachment {attachment_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch attachment"
        )

@router.put("/{attachment_id}", response_model=TaskAttachmentInDB)
async def update_attachment(
    attachment_id: str, 
    attachment: TaskAttachmentUpdate, 
    project_id: str, 
    user=Depends(verify_token), 
    role=Depends(project_rbac)
):
    """
    Update a task attachment.
    
    Required roles: owner, admin
    """
    # if role not in ["owner", "admin"]:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN, 
    #         detail="Insufficient permissions to update attachments"
    #     )
    
    try:
        # Get current attachment to verify project ownership
        current_attachment = await get_task_attachment(attachment_id)
        if not current_attachment or not hasattr(current_attachment, 'data') or not current_attachment.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Attachment not found"
            )
            
        attachment_data = current_attachment.data[0] if isinstance(current_attachment.data, list) else current_attachment.data
        
        if str(attachment_data.get('project_id')) != project_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update attachment from another project"
            )
        
        # Update the attachment with user context for history
        update_data = {
            **attachment.dict(exclude_unset=True),
            "updated_by": user["username"]
        }
        
        result = await update_task_attachment(
            attachment_id=attachment_id,
            data=update_data,
            user_id=user["username"]
        )
        
        # Handle response based on service return format
        updated_data = result.get('data', [result])[0] if hasattr(result, 'get') else result
        return updated_data
        
    except HTTPException as he:
        raise he
    except Exception as e:
        # logger.error(f"Error updating attachment {attachment_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update attachment"
        )

@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: str, 
    project_id: str, 
    hard_delete: bool = False,
    user=Depends(verify_token), 
    role=Depends(project_rbac)
):
    """
    Delete a task attachment.
    
    By default, performs a soft delete (marks as deleted but keeps the record).
    Set hard_delete=True to permanently remove the attachment.
    
    Required roles: owner
    """
    # if role != "owner":
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN, 
    #         detail="Only project owners can delete attachments"
    #     )
    
    try:
        # Get current attachment to verify project ownership
        current_attachment = await get_task_attachment(attachment_id)
        if not current_attachment or not hasattr(current_attachment, 'data') or not current_attachment.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Attachment not found"
            )
            
        attachment_data = current_attachment.data[0] if isinstance(current_attachment.data, list) else current_attachment.data
        
        if str(attachment_data.get('project_id')) != project_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete attachment from another project"
            )
        
        # Delete the attachment with user context for history
        await delete_task_attachment(
            attachment_id=attachment_id,
            user_id=user["username"],
            soft_delete=not hard_delete
        )
        
        return None  # 204 No Content
        
    except HTTPException as he:
        raise he
    except Exception as e:
        # logger.error(f"Error deleting attachment {attachment_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete attachment"
        )
    

@router.get("/", response_model=List[TaskAttachmentInDB])
async def list_attachments(
    task_id: str= Query(None),
    user=Depends(verify_token),
    # role=Depends(project_rbac)
):
    """
    List all task attachments for a project.

    Required roles: owner, admin, member, viewer
    """
    try:
        return await list_task_attachments(task_id)      
    except HTTPException as he:
        raise he
    except Exception as e:
        # logger.error(f"Error listing attachments for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list attachments"
        )