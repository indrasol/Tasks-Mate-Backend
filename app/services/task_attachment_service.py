import datetime
from typing import Dict, Any, Optional
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from app.services.task_history_service import create_task_history
from fastapi import HTTPException

async def _create_attachment_history(
    task_id: str, 
    user_id: str, 
    action: str, 
    attachment_data: Dict[str, Any],
    old_data: Optional[Dict[str, Any]] = None
) -> None:
    """Helper to create a history entry for attachment operations."""
    history_data = {
        "task_id": task_id,
        "created_by": user_id,
        "title": f"attachment_{action}",
        "metadata": {
            "attachment_id": attachment_data.get("attachment_id"),
            "title": attachment_data.get("title"),
            "filename": attachment_data.get("filename"),
            "action": action
        },
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    
    # Include old data for updates/deletions
    if old_data:
        history_data["metadata"]["old_data"] = {
            k: v for k, v in old_data.items() 
            if k in ["title", "is_inline", "deleted_at", "deleted_by"]
        }
    
    await create_task_history(history_data)

async def create_task_attachment(data: dict, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new task attachment with history tracking.
    
    Args:
        data: Attachment data including task_id, title, filename, etc.
        user_id: ID of the user performing the action (for history)
        
    Returns:
        The created attachment data
    """
    # Ensure we always have correct timestamps if not provided
    created_at = datetime.datetime.utcnow().isoformat()
    if "created_at" not in data:
        data["created_at"] = created_at
    if "uploaded_at" not in data:
        data["uploaded_at"] = created_at
    if user_id and "uploaded_by" not in data:
        data["uploaded_by"] = user_id
        
    supabase = get_supabase_client()
    def op():
        return supabase.from_("task_attachments").insert(data).execute()
    
    result = await safe_supabase_operation(op, "Failed to create task attachment")
    
    # Create history entry
    if user_id and result.data:
        attachment_data = result.data[0] if isinstance(result.data, list) else result.data
        await _create_attachment_history(
            task_id=data["task_id"],
            user_id=user_id,
            action="created",
            attachment_data=attachment_data
        )
    
    return result

async def get_task_attachment(attachment_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("task_attachments").select("*").eq("attachment_id", attachment_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch task attachment")

async def update_task_attachment(
    attachment_id: str, 
    data: dict, 
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update a task attachment with history tracking.
    
    Args:
        attachment_id: ID of the attachment to update
        data: Updated attachment data
        user_id: ID of the user performing the update (for history)
        
    Returns:
        The updated attachment data
    """
    # Get current attachment data for history
    current_attachment = await get_task_attachment(attachment_id)
    if not current_attachment or not current_attachment.data:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    current_data = current_attachment.data[0] if isinstance(current_attachment.data, list) else current_attachment.data
    
    # Update the attachment
    supabase = get_supabase_client()
    def op():
        return supabase.from_("task_attachments").update(data).eq("attachment_id", attachment_id).execute()
    
    result = await safe_supabase_operation(op, "Failed to update task attachment")
    
    # Create history entry
    if user_id and result.data:
        updated_data = result.data[0] if isinstance(result.data, list) else result.data
        await _create_attachment_history(
            task_id=current_data["task_id"],
            user_id=user_id,
            action="updated",
            attachment_data=updated_data,
            old_data=current_data
        )
    
    return result

async def delete_task_attachment(
    attachment_id: str, 
    user_id: Optional[str] = None,
    soft_delete: bool = True
) -> Dict[str, Any]:
    """
    Delete a task attachment with history tracking.
    
    Args:
        attachment_id: ID of the attachment to delete
        user_id: ID of the user performing the deletion (for history)
        soft_delete: If True, mark as deleted instead of hard delete
        
    Returns:
        The deletion result
    """
    # Get current attachment data for history
    attachment = await get_task_attachment(attachment_id)
    if not attachment or not attachment.data:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    attachment_data = attachment.data[0] if isinstance(attachment.data, list) else attachment.data
    
    if soft_delete:
        # Soft delete by marking as deleted
        delete_data = {
            "deleted_at": datetime.datetime.utcnow().isoformat(),
            "deleted_by": user_id
        }
        
        supabase = get_supabase_client()
        def op():
            return (
                supabase.from_("task_attachments")
                .update(delete_data)
                .eq("attachment_id", attachment_id)
                .execute()
            )
    else:
        # Hard delete
        supabase = get_supabase_client()
        def op():
            return (
                supabase.from_("task_attachments")
                .delete()
                .eq("attachment_id", attachment_id)
                .execute()
            )
    
    result = await safe_supabase_operation(op, "Failed to delete task attachment")
    
    # Create history entry
    if user_id and result.data:
        await _create_attachment_history(
            task_id=attachment_data["task_id"],
            user_id=user_id,
            action="deleted",
            attachment_data=attachment_data
        )
    
    return result

# ...existing code...

async def list_task_attachments(task_id: str):
    """
    List all task attachments for a given Task.

    Args:
        task_id: The ID of the Task to filter attachments.

    Returns:
        List of attachments for the Task.
    """
    supabase = get_supabase_client()
    def op():
        return (
            supabase.from_("task_attachments")
            .select("*")
            .eq("task_id", task_id)
            .is_("deleted_at", None)  # Only non-deleted attachments
            .execute()
        )
    return await safe_supabase_operation(op, "Failed to list task attachments")