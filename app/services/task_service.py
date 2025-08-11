import datetime
import json
from typing import Dict, Any, List, Tuple, Optional
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from fastapi import HTTPException
from app.services.task_history_service import create_task_history
import random

async def _generate_random_task_id() -> str:
    """Generate a random 5-digit task ID 'T{5 digits}' and ensure uniqueness."""
    supabase = get_supabase_client()
    # Avoid infinite loops; try a reasonable number of times
    for _ in range(20):
        candidate = f"T{random.randint(0, 99999):05d}"
        exists = supabase.from_("tasks").select("task_id").eq("task_id", candidate).execute()
        if not exists.data:
            return candidate
    # Fallback to time-based if collisions persist
    ts_suffix = int(datetime.datetime.utcnow().timestamp()) % 100000
    return f"T{ts_suffix:05d}"

async def _generate_sequential_task_id() -> str:
    """Generate the next sequential task ID in the format 'T000000001'."""
    supabase = get_supabase_client()
    
    def op():
        
        return (
            supabase
            .from_("tasks")
            .select("task_id")
            .order("task_id", desc=True)
            .limit(1)
            .execute()
        )

    res = await safe_supabase_operation(op, "Failed to fetch last project id")
    last_id: str | None = None
    if res and res.data:
        last_id = res.data[0]["task_id"]

    last_num = 0
    if last_id and isinstance(last_id, str) and last_id.startswith("T"):
        try:
            last_num = int(last_id[1:])
        except ValueError:
            last_num = 0

    next_num = last_num + 1
    # Pad with at least 5 digits (P00001, P00010, etc.)
    return f"T{next_num:06d}"

async def _create_task_history_entry(task_id: str, user_id: str, changes: Dict[str, Tuple[Any, Any]], action: str = "updated") -> None:
    """Helper to create a history entry for a task change."""
    if not changes:
        return
        
    history_data = {
        "task_id": task_id,
        "created_by": user_id,
        "title": action,
        "metadata": [{"field": k, "old": _serialize_value(v[0]), "new": _serialize_value(v[1])} 
                     for k, v in changes.items() if v[0] != v[1]],
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    await create_task_history(history_data)

def _serialize_value(value: Any) -> Any:
    """Helper to serialize values for history storage."""
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str)
    return value

async def _get_changes(old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Tuple[Any, Any]]:
    """Calculate changes between old and new task data."""
    changes = {}
    all_keys = set(old_data.keys()) | set(new_data.keys())
    
    for key in all_keys:
        old_val = old_data.get(key)
        new_val = new_data.get(key)
        
        # Skip metadata and internal fields
        if key in ['created_at', 'updated_at', 'history']:
            continue
            
        if old_val != new_val:
            changes[key] = (old_val, new_val)
            
    return changes

async def create_task(data: dict, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Create a new task with history tracking."""
    task_id = await _generate_sequential_task_id()
    data["task_id"] = task_id

    # Ensure we always have correct timestamps if not provided
    created_at = datetime.datetime.utcnow().isoformat()
    if "created_at" not in data:
        data["created_at"] = created_at
    if data.get("assignee"):
        data["assignee"] = str(data["assignee"])
    
    # Serialize date fields if provided
    if data.get("start_date") and hasattr(data["start_date"], "isoformat"):
        data["start_date"] = data["start_date"].isoformat()
    if data.get("due_date") and hasattr(data["due_date"], "isoformat"):
        data["due_date"] = data["due_date"].isoformat()
    
    # Insert the task
    supabase = get_supabase_client()
    def op():
        return supabase.from_("tasks").insert(data).execute()
    
    result = await safe_supabase_operation(op, "Failed to create task")
    
    # Create initial history entry
    if user_id:
        history_data = {
            "task_id": task_id,
            "created_by": user_id,
            "title": "created",
            "metadata": [{"field": k, "new": _serialize_value(v)} for k, v in data.items() 
                         if k not in ['created_at', 'updated_at', 'history']],
            "created_at": created_at
        }
        await create_task_history(history_data)
    
    return result

async def get_task(task_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("tasks").select("*").eq("task_id", task_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch task")

async def update_task(task_id: str, data: dict, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Update a task with history tracking."""
    # Get current task state
    current_task = await get_task(task_id)
    if not current_task or not current_task.data:
        raise HTTPException(status_code=404, detail="Task not found")
    
    current_data = current_task.data
    
    # Normalize the data
    if data.get("assignee"):
        data["assignee"] = str(data["assignee"])
    
    # Normalize date fields
    for date_field in ["start_date", "due_date", "completed_at"]:
        if data.get(date_field) and hasattr(data[date_field], "isoformat"):
            data[date_field] = data[date_field].isoformat()
    
    # Calculate changes
    changes = await _get_changes(current_data, data)
    
    # Update the task
    supabase = get_supabase_client()
    def op():
        return supabase.from_("tasks").update(data).eq("task_id", task_id).execute()
    
    result = await safe_supabase_operation(op, "Failed to update task")
    
    # Create history entry if there were changes and we have a user
    if changes and user_id:
        await _create_task_history_entry(task_id, user_id, changes)
    
    return result

async def add_subtask(task_id: str, subtask_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Append a subtask_id to the parent task's sub_tasks array with history tracking.
    
    Args:
        task_id: The parent task ID
        subtask_id: The subtask ID to add
        user_id: ID of the user making the change (for history)
        
    Returns:
        The updated task data
    """
    # Fetch the current task
    task_res = await get_task(task_id)
    if not task_res or not task_res.data:
        raise HTTPException(status_code=404, detail="Parent task not found")

    current_task = task_res.data
    existing_sub_tasks = current_task.get("sub_tasks") or []

    # Avoid duplicates
    if subtask_id in existing_sub_tasks:
        return task_res  # Nothing to change, return as-is

    updated_subtasks = existing_sub_tasks + [subtask_id]
    
    # Create history entry for the parent task
    if user_id:
        history_data = {
            "task_id": task_id,
            "created_by": user_id,
            "title": "subtask_added",
            "metadata": [{
                "field": "sub_tasks",
                "old": existing_sub_tasks,
                "new": updated_subtasks,
                "subtask_id": subtask_id
            }],
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        await create_task_history(history_data)

    # Persist update
    return await update_task(task_id, {"sub_tasks": updated_subtasks}, user_id)

async def remove_subtask(task_id: str, subtask_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Remove a subtask_id from the parent task's sub_tasks array with history tracking.
    
    Args:
        task_id: The parent task ID
        subtask_id: The subtask ID to remove
        user_id: ID of the user making the change (for history)
        
    Returns:
        The updated task data
    """
    task_res = await get_task(task_id)
    if not task_res or not task_res.data:
        raise HTTPException(status_code=404, detail="Parent task not found")

    current_task = task_res.data
    existing_sub_tasks = current_task.get("sub_tasks") or []

    if subtask_id not in existing_sub_tasks:
        return task_res  # Nothing to remove

    updated_subtasks = [sid for sid in existing_sub_tasks if sid != subtask_id]
    
    # Create history entry for the parent task
    if user_id:
        history_data = {
            "task_id": task_id,
            "created_by": user_id,
            "title": "subtask_removed",
            "metadata": [{
                "field": "sub_tasks",
                "old": existing_sub_tasks,
                "new": updated_subtasks,
                "subtask_id": subtask_id
            }],
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        await create_task_history(history_data)

    return await update_task(task_id, {"sub_tasks": updated_subtasks}, user_id)

async def delete_task(task_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Delete a task with history tracking."""
    # Get current task state for history
    current_task = await get_task(task_id)
    if not current_task or not current_task.data:
        raise HTTPException(status_code=404, detail="Task not found")
    
    current_data = current_task.data
    
    # Create history entry before deletion
    if user_id:
        history_data = {
            "task_id": task_id,
            "created_by": user_id,
            "title": "deleted",
            "metadata": [{"field": k, "old": _serialize_value(v)} for k, v in current_data.items() 
                         if k not in ['created_at', 'updated_at', 'history']],
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        await create_task_history(history_data)
    
    # Delete the task
    supabase = get_supabase_client()
    def op():
        return supabase.from_("tasks").delete().eq("task_id", task_id).execute()
    
    return await safe_supabase_operation(op, "Failed to delete task")

async def get_all_tasks(
    search: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "title",
    sort_order: str = "asc",
    status: Optional[str] = None,
    org_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get all tasks with optional filtering, sorting, and history inclusion.
    
    Args:
        search: Text to search in task titles
        limit: Maximum number of tasks to return
        offset: Number of tasks to skip
        sort_by: Field to sort by
        sort_order: Sort order ('asc' or 'desc')
        status: Filter by task status
        org_id: Filter by organization ID
        include_history: Whether to include task history
        
    Returns:
        List of task dictionaries
    """
    supabase = get_supabase_client()
    
    # Base query
    query = supabase.from_("task_card_view").select("*")
    
    # Apply filters
    if search:
        query = query.ilike("title", f"%{search}%")
    if status:
        query = query.eq("status", status)
    if org_id:
        query = query.eq("org_id", org_id)
    
    # Apply sorting
    query = query.order(sort_by, desc=(sort_order.lower() == "desc"))
    
    # Apply pagination
    result = query.range(offset, offset + limit - 1).execute()
    tasks = result.data or []
    
    # Include history if requested
    # if include_history and tasks:
    #     task_ids = [task['task_id'] for task in tasks]
    #     history = await get_tasks_history(task_ids)
    #     history_map = {h['task_id']: h for h in history}
        
    #     for task in tasks:
    #         task['history'] = history_map.get(task['task_id'], [])
    
    return tasks

async def get_tasks_for_project(
    project_id: str,
    search: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "title",
    sort_order: str = "asc",
    status: Optional[str] = None,
    org_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get tasks for a specific project with optional filtering, sorting, and history.
    
    Args:
        project_id: ID of the project to get tasks for
        search: Text to search in task titles
        limit: Maximum number of tasks to return
        offset: Number of tasks to skip
        sort_by: Field to sort by
        sort_order: Sort order ('asc' or 'desc')
        status: Filter by task status
        org_id: Filter by organization ID
        include_history: Whether to include task history
        
    Returns:
        List of task dictionaries for the project
    """
    supabase = get_supabase_client()
    
    # Base query with project filter
    query = supabase.from_("task_card_view").select("*").eq("project_id", project_id)
    
    # Apply additional filters
    if search:
        query = query.ilike("title", f"%{search}%")
    if status:
        query = query.eq("status", status)
    if org_id:
        query = query.eq("org_id", org_id)
    
    # Apply sorting
    query = query.order(sort_by, desc=(sort_order.lower() == "desc"))
    
    # Apply pagination
    result = query.range(offset, offset + limit - 1).execute()
    tasks = result.data or []
    
    # Include history if requested
    # if include_history and tasks:
    #     task_ids = [task['task_id'] for task in tasks]
    #     history = await get_tasks_history(task_ids)
    #     history_map = {h['task_id']: h for h in history}
        
    #     for task in tasks:
    #         task['history'] = history_map.get(task['task_id'], [])
    
    return tasks