import random
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import HTTPException, UploadFile
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from app.models.schemas.bug import (
    BugCreate, BugUpdate, BugCommentCreate, BugCommentUpdate, BugRelationCreate,
    
)

from app.models.enums import BugStatusEnum, BugPriorityEnum, BugTypeEnum


async def _generate_sequential_bug_id() -> str:
    """Generate a random task ID with prefix 'T' and 6 digits, ensuring uniqueness."""
    supabase = get_supabase_client()
    digits = 6
    for _ in range(10):
        candidate = f"B{random.randint(0, 10**digits - 1):0{digits}d}"
        def op():
            return supabase.from_("bugs").select("id").eq("id", candidate).limit(1).execute()
        res = await safe_supabase_operation(op, "Failed to verify task id uniqueness")
        if not res or not getattr(res, "data", None):
            return candidate
    # Fallback: time-based suffix to reduce collision risk
    ts = int(datetime.datetime.utcnow().timestamp()) % (10**digits)
    return f"B{ts:0{digits}d}"


async def _generate_sequential_bug_log_id() -> str:
    """Generate a random task ID with prefix 'T' and 6 digits, ensuring uniqueness."""
    supabase = get_supabase_client()
    digits = 8
    for _ in range(10):
        candidate = f"L{random.randint(0, 10**digits - 1):0{digits}d}"
        def op():
            return supabase.from_("bugs").select("id").eq("id", candidate).limit(1).execute()
        res = await safe_supabase_operation(op, "Failed to verify task id uniqueness")
        if not res or not getattr(res, "data", None):
            return candidate
    # Fallback: time-based suffix to reduce collision risk
    ts = int(datetime.datetime.utcnow().timestamp()) % (10**digits)
    return f"L{ts:0{digits}d}"

# Bug CRUD Operations
async def create_bug(bug_data: BugCreate, username: str) -> Dict[str, Any]:
    """Create a new bug with history tracking."""
    supabase = get_supabase_client()
    
    # Prepare bug data
    bug_dict = bug_data.dict(exclude_unset=True)

    """Create a new task with history tracking."""
    task_id = await _generate_sequential_bug_id()
    bug_dict["id"] = task_id

    bug_dict.update({
        "reporter": username,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    })
    
    # Insert bug
    def op():
        return supabase.from_("bugs").insert(bug_dict).execute()
    
    result = await safe_supabase_operation(op, "Failed to create bug")
    
    # Log the creation activity
    if result.data:
        await _log_bug_activity(
            bug_id=result.data[0]["id"],
            username=username,
            activity_type="bug_created",
            new_value=bug_dict
        )
    
    return result

async def get_bug(bug_id: str) -> Dict[str, Any]:
    """Get a bug by ID with related data."""
    supabase = get_supabase_client()
    
    # def op():
    #     return supabase.rpc('get_bug_with_relations', {'bug_id': bug_id}).execute()
    def op():
        return supabase.from_('bugs').select('*').eq('id',bug_id).execute()
    
    result = await safe_supabase_operation(op, "Failed to fetch bug")
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Bug not found")
        
    return result.data[0] if result.data else None

async def update_bug(bug_id: str, bug_data: BugUpdate, username: str) -> Dict[str, Any]:
    """Update a bug and log changes."""
    # Get current bug data
    current_bug = await get_bug(bug_id)
    if not current_bug:
        raise HTTPException(status_code=404, detail="Bug not found")
    
    # Prepare update data
    update_data = bug_data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    # Calculate changes for activity log
    changes = {}
    for key, new_value in update_data.items():
        if key in current_bug and current_bug[key] != new_value:
            changes[key] = {
                "old": current_bug.get(key),
                "new": new_value
            }
    
    # Update bug
    supabase = get_supabase_client()
    
    def op():
        return supabase.from_("bugs").update(update_data).eq("id", bug_id).execute()
    
    result = await safe_supabase_operation(op, "Failed to update bug")
    
    # Log the update activity if there were changes
    if changes and result.data:
        await _log_bug_activity(
            bug_id=bug_id,
            username=username,
            activity_type="bug_updated",
            old_value=changes,
            new_value=update_data
        )
    
    return result

async def delete_bug(bug_id: str, username: str) -> Dict[str, Any]:
    """Delete a bug and log the deletion."""
    # Get bug data before deletion for logging
    bug_data = await get_bug(bug_id)
    if not bug_data:
        raise HTTPException(status_code=404, detail="Bug not found")
    
    # Delete bug
    supabase = get_supabase_client()
    
    def op():
        return supabase.from_("bugs").delete().eq("id", bug_id).execute()
    
    result = await safe_supabase_operation(op, "Failed to delete bug")
    
    # Log the deletion
    if result.data:
        await _log_bug_activity(
            bug_id=bug_id,
            username=username,
            activity_type="bug_deleted",
            old_value=bug_data
        )
    
    return result

# Bug Comments
async def create_bug_comment(bug_id: str, comment_data: BugCommentCreate, username: str) -> Dict[str, Any]:
    """Add a comment to a bug."""
    supabase = get_supabase_client()
    
    comment_dict = comment_data.model_dump()
    comment_dict.update({
        "bug_id": bug_id,
        "user_id": username,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    })
    
    def op():
        return supabase.from_("bug_comments").insert(comment_dict).execute()
    
    result = await safe_supabase_operation(op, "Failed to add comment")
    
    # Log the comment activity
    if result.data:
        await _log_bug_activity(
            bug_id=bug_id,
            username=username,
            activity_type="comment_added",
            new_value={"comment_id": result.data[0]["id"], "content": comment_data.content[:100]}
        )
    
    return result

async def update_bug_comment(comment_id: str, comment_data: BugCommentUpdate, username: str) -> Dict[str, Any]:
    """Update a comment on a bug."""
    supabase = get_supabase_client()
    
    comment_dict = comment_data.model_dump()
    comment_dict.update({
        "updated_at": datetime.utcnow().isoformat()
    })
    
    def op():
        return supabase.from_("bug_comments").update(comment_dict).eq("id", comment_id).execute()
    
    result = await safe_supabase_operation(op, "Failed to update comment")
    
    # Log the comment update activity
    if result.data:
        await _log_bug_activity(
            bug_id=comment_data.bug_id,
            username=username,
            activity_type="comment_updated",
            old_value={"comment_id": comment_id, "content": comment_data.content[:100]},
            new_value={"comment_id": comment_id, "content": comment_data.content[:100]}
        )
    
    return result

async def get_bug_comments(bug_id: str) -> List[Dict[str, Any]]:
    """Get all comments for a bug."""
    supabase = get_supabase_client()
    
    def op():
        return supabase.from_("bug_comments_with_user") \
                     .select("*") \
                     .eq("bug_id", bug_id) \
                     .order("created_at") \
                     .execute()
    
    result = await safe_supabase_operation(op, "Failed to fetch comments")
    return result.data if result.data else []

# Bug Attachments
async def create_bug_attachment(bug_id: str, file: UploadFile, username: str) -> Dict[str, Any]:
    """Add an attachment to a bug."""
    # Upload file to storage
    file_content = await file.read()
    file_path = f"bug_attachments/{bug_id}/{uuid.uuid4()}_{file.filename}"
    
    supabase = get_supabase_client()
    
    def upload_op():
        return supabase.storage.from_("attachments").upload(file_path, file_content)
    
    upload_result = await safe_supabase_operation(upload_op, "Failed to upload file")
    
    if not upload_result:
        raise HTTPException(status_code=500, detail="Failed to upload file")
    
    # Create attachment record
    attachment_data = {
        "bug_id": bug_id,
        "user_id": username,
        "file_name": file.filename,
        "file_path": file_path,
        "file_type": file.content_type,
        "file_size": len(file_content),
        "created_at": datetime.utcnow().isoformat()
    }
    
    def insert_op():
        return supabase.from_("bug_attachments").insert(attachment_data).execute()
    
    result = await safe_supabase_operation(insert_op, "Failed to create attachment record")
    
    # Log the attachment activity
    if result.data:
        await _log_bug_activity(
            bug_id=bug_id,
            username=username,
            activity_type="attachment_added",
            new_value={"file_name": file.filename, "file_size": len(file_content)}
        )
    
    return result

# Bug Attachments

async def list_bug_attachments(bug_id: str) -> List[Dict[str, Any]]:
    """List all attachments for a bug."""
    supabase = get_supabase_client()
    
    def op():
        return (
            supabase.from_("bug_attachments")
            .select("*")
            .eq("bug_id", bug_id)
            .order("created_at", desc=True)
            .execute()
        )
    
    result = await safe_supabase_operation(op, "Failed to list bug attachments")
    return result.data if result.data else []

async def get_bug_attachment(attachment_id: str) -> Optional[Dict[str, Any]]:
    """Get a bug attachment by ID."""
    supabase = get_supabase_client()
    
    def op():
        return supabase.from_("bug_attachments").select("*").eq("id", attachment_id).single().execute()
    
    result = await safe_supabase_operation(op, "Failed to fetch bug attachment")
    return result.data if result.data else None

async def upload_bug_attachment(
    bug_id: str,
    file: UploadFile,
    username: str,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Upload and attach a file to a bug."""
    # Read file content
    file_content = await file.read()
    
    # Generate a unique filename
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else ''
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = f"bug_attachments/{bug_id}/{file_name}"
    
    # Upload to storage
    supabase = get_supabase_client()
    
    def upload_op():
        return supabase.storage.from_("bug-attachments").upload(file_path, file_content)
    
    upload_result = await safe_supabase_operation(upload_op, "Failed to upload file")
    
    if not upload_result:
        raise HTTPException(status_code=500, detail="Failed to upload file to storage")
    
    # Get public URL
    def get_url_op():
        return supabase.storage.from_("bug-attachments").get_public_url(file_path)
    
    public_url = await safe_supabase_operation(get_url_op, "Failed to get file URL")
    
    # Create attachment record
    attachment_data = {
        "bug_id": bug_id,
        "file_name": file.filename,
        "file_path": file_path,
        "file_type": file.content_type,
        "file_size": len(file_content),
        "user_id": username,
        "description": description,
        "url": public_url,
        "created_at": datetime.utcnow().isoformat()
    }
    
    def insert_op():
        return supabase.from_("bug_attachments").insert(attachment_data).execute()
    
    result = await safe_supabase_operation(insert_op, "Failed to create attachment record")
    
    # Log the attachment activity
    if result.data:
        await _log_bug_activity(
            bug_id=bug_id,
            username=username,
            activity_type="attachment_added",
            new_value={"file_name": file.filename, "file_size": len(file_content)}
        )
    
    return result.data[0] if result.data else None

async def delete_bug_attachment(attachment_id: str, username: str) -> bool:
    """Delete a bug attachment by ID."""
    # Get attachment data first
    attachment = await get_bug_attachment(attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    # Delete from storage
    supabase = get_supabase_client()
    
    def delete_storage_op():
        return supabase.storage.from_("bug-attachments").remove([attachment["file_path"]])
    
    # Even if storage deletion fails, we'll still try to delete the DB record
    await safe_supabase_operation(delete_storage_op, "Failed to delete file from storage")
    
    # Delete the record
    def delete_db_op():
        return supabase.from_("bug_attachments").delete().eq("id", attachment_id).execute()
    
    result = await safe_supabase_operation(delete_db_op, "Failed to delete attachment record")
    
    # Log the deletion
    if result.data:
        await _log_bug_activity(
            bug_id=attachment["bug_id"],
            username=username,
            activity_type="attachment_removed",
            old_value={"file_name": attachment["file_name"]}
        )
    
    return len(result.data) > 0 if result.data else False

# Bug Watchers
async def add_bug_watcher(bug_id: str, username: str) -> Dict[str, Any]:
    """Add a user as a watcher to a bug."""
    supabase = get_supabase_client()
    
    watcher_data = {
        "bug_id": bug_id,
        "user_id": username,
        "created_at": datetime.utcnow().isoformat()
    }
    
    def op():
        return supabase.from_("bug_watchers").insert(watcher_data).execute()
    
    result = await safe_supabase_operation(op, "Failed to add watcher")
    
    # Log the watcher addition
    if result.data:
        await _log_bug_activity(
            bug_id=bug_id,
            username=username,
            activity_type="watcher_added",
            new_value={"watcher": username}
        )
    
    return result

# Bug Watchers

async def add_bug_watcher(bug_id: str, username: str) -> Dict[str, Any]:
    """Add a user as a watcher to a bug."""
    # Check if the bug exists
    bug = await get_bug(bug_id)
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")
    
    # Check if user is already a watcher
    existing = await get_bug_watcher(bug_id, username)
    if existing:
        return existing
    
    # Add watcher
    supabase = get_supabase_client()
    watcher_data = {
        "bug_id": bug_id,
        "user_id": username,
        "created_at": datetime.utcnow().isoformat()
    }
    
    def op():
        return supabase.from_("bug_watchers").insert(watcher_data).execute()
    
    result = await safe_supabase_operation(op, "Failed to add watcher")
    
    # Log the activity
    if result.data:
        await _log_bug_activity(
            bug_id=bug_id,
            username=username,
            activity_type="watcher_added",
            new_value={"watcher": username}
        )
    
    return result.data[0] if result.data else None

async def remove_bug_watcher(bug_id: str, username: str) -> bool:
    """Remove a user from bug watchers."""
    supabase = get_supabase_client()
    
    def op():
        return (
            supabase.from_("bug_watchers")
            .delete()
            .eq("bug_id", bug_id)
            .eq("user_id", username)
            .execute()
        )
    
    result = await safe_supabase_operation(op, "Failed to remove watcher")
    
    # Log the activity if the watcher was removed
    if result.data and len(result.data) > 0:
        await _log_bug_activity(
            bug_id=bug_id,
            username=username,
            activity_type="watcher_removed",
            old_value={"watcher": username}
        )
        return True
    
    return False

async def get_bug_watcher(bug_id: str, username: str) -> Optional[Dict[str, Any]]:
    """Check if a user is watching a bug."""
    supabase = get_supabase_client()
    
    def op():
        return (
            supabase.from_("bug_watchers")
            .select("*")
            .eq("bug_id", bug_id)
            .eq("user_id", username)
            .maybe_single()
            .execute()
        )
    
    result = await safe_supabase_operation(op, "Failed to check watcher status")
    return result.data if result.data else None

async def list_bug_watchers(bug_id: str) -> List[Dict[str, Any]]:
    """List all watchers for a bug."""
    supabase = get_supabase_client()
    
    def op():
        return (
            supabase.from_("bug_watchers")
            .select("*")
            .eq("bug_id", bug_id)
            .order("created_at", desc=True)
            .execute()
        )
    
    result = await safe_supabase_operation(op, "Failed to list watchers")
    return result.data if result.data else []


# Bug Relations
async def create_bug_relation(
    source_bug_id: str, 
    relation_data: BugRelationCreate, 
    username: str
) -> Dict[str, Any]:
    """Create a relation between two bugs."""
    supabase = get_supabase_client()
    
    relation_dict = relation_data.dict()
    relation_dict.update({
        "source_bug_id": source_bug_id,
        "created_by": username,
        "created_at": datetime.utcnow().isoformat()
    })
    
    def op():
        return supabase.from_("bug_relations").insert(relation_dict).execute()
    
    result = await safe_supabase_operation(op, "Failed to create bug relation")
    
    # Log the relation creation
    if result.data:
        await _log_bug_activity(
            bug_id=source_bug_id,
            username=username,
            activity_type="relation_created",
            new_value={
                "target_bug_id": relation_data.target_bug_id,
                "relation_type": relation_data.relation_type
            }
        )
    
    return result


# Bug Relations

async def create_bug_relation(
    source_bug_id: str,
    target_bug_id: str,
    relation_type: str,
    username: str,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a relationship between two bugs.
    
    Common relation types:
    - 'duplicate': source is a duplicate of target
    - 'blocked_by': source is blocked by target
    - 'blocks': source blocks target
    - 'related_to': source is related to target
    - 'parent': source is a parent of target
    - 'child': source is a child of target
    """
    # Check if both bugs exist
    source_bug = await get_bug(source_bug_id)
    if not source_bug:
        raise HTTPException(status_code=404, detail="Source bug not found")
        
    target_bug = await get_bug(target_bug_id)
    if not target_bug:
        raise HTTPException(status_code=404, detail="Target bug not found")
    
    # Prevent self-referential relationships
    if source_bug_id == target_bug_id:
        raise HTTPException(status_code=400, detail="Cannot create a self-referential relationship")
    
    # Check if the relationship already exists
    existing = await get_bug_relation(source_bug_id, target_bug_id, relation_type)
    if existing:
        return existing
    
    supabase = get_supabase_client()
    relation_data = {
        "source_bug_id": source_bug_id,
        "target_bug_id": target_bug_id,
        "relation_type": relation_type,
        "created_by": username,
        "description": description,
        "created_at": datetime.utcnow().isoformat()
    }
    
    def op():
        return supabase.from_("bug_relations").insert(relation_data).execute()
    
    result = await safe_supabase_operation(op, "Failed to create bug relation")
    
    # Log the relation creation
    if result.data:
        await _log_bug_activity(
            bug_id=source_bug_id,
            username=username,
            activity_type=f"relation_created_{relation_type}",
            new_value={
                "target_bug_id": target_bug_id,
                "target_bug_title": target_bug.get("title"),
                "relation_type": relation_type,
                "description": description
            }
        )
        
        # Also log on the target bug if it's a blocking relationship
        if relation_type in ['blocks', 'duplicate']:
            await _log_bug_activity(
                bug_id=target_bug_id,
                username=username,
                activity_type=f"related_bug_{relation_type}_created",
                new_value={
                    "source_bug_id": source_bug_id,
                    "source_bug_title": source_bug.get("title"),
                    "relation_type": relation_type,
                    "description": description
                }
            )
    
    return result.data[0] if result.data else None

async def delete_bug_relation(relation_id: str, username: str) -> bool:
    """Delete a bug relation by ID."""
    # Get the relation first to log the deletion
    relation = await get_bug_relation_by_id(relation_id)
    if not relation:
        raise HTTPException(status_code=404, detail="Relation not found")
    
    supabase = get_supabase_client()
    
    def op():
        return supabase.from_("bug_relations").delete().eq("id", relation_id).execute()
    
    result = await safe_supabase_operation(op, "Failed to delete bug relation")
    
    # Log the deletion
    if result.data and len(result.data) > 0:
        source_bug_id = relation["source_bug_id"]
        target_bug_id = relation["target_bug_id"]
        relation_type = relation["relation_type"]
        
        await _log_bug_activity(
            bug_id=source_bug_id,
            username=username,
            activity_type=f"relation_removed_{relation_type}",
            old_value={
                "target_bug_id": target_bug_id,
                "relation_type": relation_type
            }
        )
        
        # Also log on the target bug if it was a blocking relationship
        if relation_type in ['blocks', 'duplicate']:
            await _log_bug_activity(
                bug_id=target_bug_id,
                username=username,
                activity_type=f"related_bug_{relation_type}_removed",
                old_value={
                    "source_bug_id": source_bug_id,
                    "relation_type": relation_type
                }
            )
        
        return True
    
    return False

async def get_bug_relation(
    source_bug_id: str,
    target_bug_id: str,
    relation_type: str
) -> Optional[Dict[str, Any]]:
    """Get a specific relation between two bugs."""
    supabase = get_supabase_client()
    
    def op():
        return (
            supabase.from_("bug_relations")
            .select("*")
            .eq("source_bug_id", source_bug_id)
            .eq("target_bug_id", target_bug_id)
            .eq("relation_type", relation_type)
            .maybe_single()
            .execute()
        )
    
    result = await safe_supabase_operation(op, "Failed to get bug relation")
    return result.data if result.data else None

async def get_bug_relation_by_id(relation_id: str) -> Optional[Dict[str, Any]]:
    """Get a bug relation by its ID."""
    supabase = get_supabase_client()
    
    def op():
        return supabase.from_("bug_relations").select("*").eq("id", relation_id).single().execute()
    
    result = await safe_supabase_operation(op, "Failed to get bug relation by ID")
    return result.data if result.data else None

async def list_bug_relations(
    bug_id: str,
    relation_type: Optional[str] = None,
    direction: str = "both"
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List all relations for a bug.
    
    Args:
        bug_id: The ID of the bug to get relations for
        relation_type: Optional filter by relation type
        direction: 'incoming', 'outgoing', or 'both' (default)
    """
    supabase = get_supabase_client()
    result = {"incoming": [], "outgoing": []}
    
    # Get outgoing relations (where this bug is the source)
    if direction in ["both", "outgoing"]:
        def outgoing_op():
            query = (
                supabase.from_("bug_relations")
                .select("*, target_bug:target_bug_id(id, title, status, priority)")
                .eq("source_bug_id", bug_id)
            )
            if relation_type:
                query = query.eq("relation_type", relation_type)
            return query.execute()
        
        outgoing_result = await safe_supabase_operation(outgoing_op, "Failed to get outgoing relations")
        if outgoing_result.data:
            result["outgoing"] = outgoing_result.data
    
    # Get incoming relations (where this bug is the target)
    if direction in ["both", "incoming"]:
        def incoming_op():
            query = (
                supabase.from_("bug_relations")
                .select("*, source_bug:source_bug_id(id, title, status, priority)")
                .eq("target_bug_id", bug_id)
            )
            if relation_type:
                query = query.eq("relation_type", relation_type)
            return query.execute()
        
        incoming_result = await safe_supabase_operation(incoming_op, "Failed to get incoming relations")
        if incoming_result.data:
            result["incoming"] = incoming_result.data
    
    return result



# Helper function to log bug activities
async def _log_bug_activity(
    bug_id: str,
    username: str,
    activity_type: str,
    old_value: Optional[Dict] = None,
    new_value: Optional[Dict] = None
) -> None:
    """Log an activity related to a bug."""

    """Create a new task with history tracking."""
    log_id = await _generate_sequential_bug_log_id()

    supabase = get_supabase_client()
    
    activity_data = {
        "id":log_id,
        "bug_id": bug_id,
        "user_id": username,
        "activity_type": activity_type,
        "old_value": old_value,
        "new_value": new_value,
        "created_at": datetime.utcnow().isoformat()
    }
    
    def op():
        return supabase.from_("bug_activity_logs").insert(activity_data).execute()
    
    await safe_supabase_operation(op, "Failed to log activity")

async def get_bug_activity_logs(bug_id: str) -> List[Dict[str, Any]]:
    """Get activity logs for a bug."""
    supabase = get_supabase_client()
    
    def op():
        return supabase.from_("bug_activity_logs").select("*").eq("bug_id", bug_id).execute()
    
    result = await safe_supabase_operation(op, "Failed to fetch activity logs")
    return result.data if result.data else []

async def get_activity_detail(bug_id: str, activity_id: str) -> Dict[str, Any]:
    """Get details of a specific activity log entry."""
    supabase = get_supabase_client()
    
    def op():
        return supabase.from_("bug_activity_logs").select("*").eq("bug_id", bug_id).eq("id", activity_id).execute()
    
    result = await safe_supabase_operation(op, "Failed to fetch activity detail")
    return result.data[0] if result.data else None

# Search and filter bugs
async def search_bugs(
    tracker_id: str,
    project_id: Optional[str] = None,
    status: Optional[List[BugStatusEnum]] = None,
    priority: Optional[List[BugPriorityEnum]] = None,
    type: Optional[List[BugTypeEnum]] = None,
    assignee: Optional[List[str]] = None,
    reporter: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    search_query: Optional[str] = None,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """Search and filter bugs with pagination."""
    supabase = get_supabase_client()
    
    # Build the query
    # query = supabase.from_("bug_details").select("*", count="exact")
    query = supabase.from_("bugs").select("*", count="exact")

    
    # Apply filters
    if tracker_id:
        query = query.eq("tracker_id", tracker_id)
    if project_id:
        query = query.eq("project_id", project_id)
    if status:
        query = query.in_("status", [s.value for s in status])
    if priority:
        query = query.in_("priority", [p.value for p in priority])
    if type:
        query = query.in_("type", [t.value for t in type])
    if assignee:
        query = query.in_("assignee", assignee)
    if reporter:
        query = query.in_("reporter", reporter)
    if tags:
        query = query.contains("tags", tags)
    if search_query:
        query = query.or_(f"title.ilike.%{search_query}%,description.ilike.%{search_query}%")
    
    # Apply sorting
    if sort_order.lower() == "asc":
        query = query.order(sort_by, desc=False)
    else:
        query = query.order(sort_by, desc=True)
    
    # Apply pagination
    start = (page - 1) * page_size
    end = start + page_size - 1
    query = query.range(start, end)
    
    # Execute the query
    def op():
        return query.execute()
    
    result = await safe_supabase_operation(op, "Failed to search bugs")
    
    return {
        "data": result.data if result.data else [],
        "total": result.count if hasattr(result, 'count') else 0,
        "page": page,
        "page_size": page_size
    }
