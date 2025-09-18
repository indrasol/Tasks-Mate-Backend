import datetime
import json
from typing import Dict, Any, List, Tuple, Optional
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from fastapi import HTTPException
from app.services.task_history_service import create_task_history, record_history
import random

async def _generate_sequential_task_id() -> str:
    """Generate a random task ID with prefix 'T' and 6 digits, ensuring uniqueness."""
    supabase = get_supabase_client()
    digits = 6
    for _ in range(10):
        candidate = f"T{random.randint(0, 10**digits - 1):0{digits}d}"
        def op():
            return supabase.from_("tasks").select("task_id").eq("task_id", candidate).limit(1).execute()
        res = await safe_supabase_operation(op, "Failed to verify task id uniqueness")
        if not res or not getattr(res, "data", None):
            return candidate
    # Fallback: time-based suffix to reduce collision risk
    ts = int(datetime.datetime.utcnow().timestamp()) % (10**digits)
    return f"T{ts:0{digits}d}"

# ────────────────────────────────────────────────────────────
# Diff helpers (whitelist)
# ────────────────────────────────────────────────────────────

UPDATE_WHITELIST = [
    "title",
    "description",
    "status",
    "priority",
    "start_date",
    "due_date",
    "completed_at",
    "tags",
    "project_id",
    "assignee",
    # NOTE: sub_tasks / dependencies are handled by dedicated endpoints
]

def _norm(v: Any):
    if v is None:
        return None
    if isinstance(v, datetime.datetime):
        # Persist stable date format for diffs
        return v.replace(microsecond=0).isoformat()
    if isinstance(v, datetime.date):
        return v.isoformat()
    return v

def _compute_task_diff(before: Dict[str, Any], after: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Returns a list of {field, old, new} only for whitelisted fields that changed.
    Keeps arrays/objects as-is (no stringifying).
    """
    changes: List[Dict[str, Any]] = []
    for field in UPDATE_WHITELIST:
        old = _norm(before.get(field))
        new = _norm(after.get(field))
        # Normalize arrays (e.g., tags) to avoid order noise
        if isinstance(old, list):
            old = sorted(old)
        if isinstance(new, list):
            new = sorted(new)
        if old != new:
            changes.append({"field": field, "old": old, "new": new})
    return changes

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


async def create_task(data: dict, user_name: Optional[str] = None, actor_display: Optional[str] = None) -> Dict[str, Any]:
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

    bug_id = data["bug_id"]
    data.pop("bug_id", None)

    tracker_id = data["tracker_id"]
    data.pop("tracker_id", None)
    
    # Insert the task
    supabase = get_supabase_client()
    def op():
        return supabase.from_("tasks").insert(data).execute()
    
    result = await safe_supabase_operation(op, "Failed to create task")
    print(f"Task created: {data.get('title')}")
    
    # Create initial history entry
    if result.data:
        await record_history(
            task_id=task_id,
            action="created",
            created_by=data.get("created_by"),
            title=data.get("title"),
            metadata=[],  # keep 'created' clean; the snapshot can be large—prefer UI shows created event only
            actor_display=actor_display,
        )    

    if bug_id or tracker_id:
        data["bug_id"] = bug_id
        data["tracker_id"] = tracker_id
        await create_tracker_task(data, user_name, actor_display)

    return result


async def create_tracker_task(data: dict, user_name: Optional[str] = None, actor_display: Optional[str] = None) -> Dict[str, Any]:
    """Create a new task with history tracking."""

    # Ensure we always have correct timestamps if not provided
    created_at = datetime.datetime.utcnow().isoformat()
    if "created_at" not in data:
        data["created_at"] = created_at

    tracker_data = {}

    tracker_data["tracker_id"] = data["tracker_id"]
    tracker_data["bug_id"] = data["bug_id"]
    tracker_data["task_id"] = data["task_id"]
    tracker_data["created_at"] = data["created_at"]
    
    # Insert the task
    supabase = get_supabase_client()
    def op():
        return supabase.from_("test_tracker_tasks").insert(tracker_data).execute()
    
    result = await safe_supabase_operation(op, "Failed to create task tracker")
    print(f"Task Tracker created: {data.get('title')}")

    changes: List[Dict[str, Any]] = []

    changes.append({"field": "bug_id", "old": None, "new": data["bug_id"]})
    changes.append({"field": "tracker_id", "old": None, "new": data["tracker_id"]})
    
    # Create initial history entry
    if result.data:
        await record_history(
            task_id=data["task_id"],
            action="updated",
            created_by=data.get("created_by"),
            title=data.get("title"),
            metadata=changes,  # keep 'created' clean; the snapshot can be large—prefer UI shows created event only
            actor_display=actor_display,
        )
    return result


async def delete_tracker_task(task_id: str, bug_id: str, user_id: Optional[str] = None, actor_display: Optional[str] = None) -> Dict[str, Any]:
    """Delete a task and log 'deleted' before removal (so audit survives hard delete)."""
    current_task = await get_task(task_id)
    if not current_task or not current_task.data:
        raise HTTPException(status_code=404, detail="Task not found")
    before = current_task.data

    changes: List[Dict[str, Any]] = []

    changes.append({"field": "bug_id", "old": before["bug_id"], "new": None})
    changes.append({"field": "tracker_id", "old": before["tracker_id"], "new": None})
    

    if user_id:
        await record_history(
            task_id=task_id,
            action="updated",
            created_by=user_id,
            title=before.get("title"),
            metadata=changes,  # keep small; you can include a few key fields if desired
            actor_display=actor_display,
        )

    supabase = get_supabase_client()

    def op():
        return supabase.from_("test_tracker_tasks").delete().eq("task_id", task_id).eq("bug_id", bug_id).execute()

    return await safe_supabase_operation(op, "Failed to delete task")

async def get_task(task_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("task_card_view").select("*").eq("task_id", task_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch task")

async def update_task(
    task_id: str,
    data: dict,
    user_id: Optional[str] = None,
    suppress_history: bool = False,
    actor_display: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update a task; compute a whitelisted diff; write ONE 'updated' history event with the diff.
    """
    # 1) Fetch current
    current_res = await get_task(task_id)
    if not current_res or not current_res.data:
        raise HTTPException(status_code=404, detail="Task not found")
    before: Dict[str, Any] = current_res.data

    # 2) Normalize incoming payload
    payload: Dict[str, Any] = {}
    for k in UPDATE_WHITELIST + ["assignee", "sub_tasks", "dependencies"] + ["is_subtask"]:
        if k in data:
            payload[k] = data[k]

    # Convert Enum values (from pydantic TaskUpdate) to their raw values for DB/logic
    if "status" in payload and hasattr(payload["status"], "value"):
        payload["status"] = str(payload["status"].value)
    if "priority" in payload and hasattr(payload["priority"], "value"):
        payload["priority"] = str(payload["priority"].value)

    if "assignee" in payload and payload["assignee"] is not None:
        payload["assignee"] = str(payload["assignee"])

    for df in ["start_date", "due_date", "completed_at"]:
        if isinstance(payload.get(df), (datetime.datetime, datetime.date)):
            payload[df] = _norm(payload[df])
    
    # Guard: block status -> completed if any dependency (after this update) is not completed
    status_raw = payload.get("status")
    if status_raw is None:
        status_raw = before.get("status")
        if hasattr(status_raw, "value"):
            status_raw = status_raw.value
    print("status_raw", status_raw)
    try_set_completed = (str(status_raw or "").lower() == "completed")
    print("try_set_completed", try_set_completed)
    if try_set_completed:
        # dependencies after this update (if provided), otherwise current ones (normalize when DB returns JSON as string)
        deps_after: List[str] | None = payload.get("dependencies")
        if deps_after is None:
            raw = before.get("dependencies") or []
            if isinstance(raw, str):
                try:
                    parsed = json.loads(raw)
                    deps_after = parsed if isinstance(parsed, list) else []
                except Exception:
                    deps_after = []
            elif isinstance(raw, list):
                deps_after = raw
            else:
                deps_after = []
        # ensure list of strings
        if not isinstance(deps_after, list):
            deps_after = []
        else:
            deps_after = [str(x) for x in deps_after if x is not None]
        # Only check when there *are* dependencies
        if deps_after:
            # Trim and uniq dependency ids
            deps_after = sorted({str(x).strip() for x in deps_after if x})
            sb = get_supabase_client()
            def dep_op():
                return (
                    sb.from_("tasks")
                    .select("task_id,status")
                    .in_("task_id", deps_after)
                    .execute()
                )
            dep_res = await safe_supabase_operation(dep_op, "Failed to validate dependencies")
            rows = dep_res.data or []
            found_ids = {str(r.get("task_id")).strip() for r in rows}
            # Any missing ids are treated as incomplete safeguards
            missing = [d for d in deps_after if d not in found_ids]
            # Consider ONLY exact 'completed' as satisfied among found
            not_completed = [str(r.get("task_id")) for r in rows if str(r.get("status") or "").lower() != "completed"]
            incomplete = missing + not_completed
            if incomplete:
                # Show up to first 5 ids for a friendly error
                preview = ", ".join(incomplete[:5])
                more = f" (+{len(incomplete)-5} more)" if len(incomplete) > 5 else ""
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot mark task as completed while {len(incomplete)} in complete dependency(ies): {preview}{more}"
                )


    # 3) Compute diff against *final* state that would be saved
    after = {**before, **payload}
    changes = _compute_task_diff(before, after)

    # 4) Persist update (even if no changes; supabase will no-op)
    supabase = get_supabase_client()

    def op():
        return supabase.from_("tasks").update(payload).eq("task_id", task_id).execute()

    result = await safe_supabase_operation(op, "Failed to update task")

    # 5) Record history (one compact event)
    if changes and user_id and not suppress_history:
        await record_history(
            task_id=task_id,
            action="updated",
            created_by=user_id,
            title=after.get("title") or before.get("title"),
            metadata=changes,  # jsonb[] of {field,old,new}
            actor_display=actor_display,
        )

    return result


async def delete_task(task_id: str, user_id: Optional[str] = None, actor_display: Optional[str] = None) -> Dict[str, Any]:
    """Delete a task and log 'deleted' before removal (so audit survives hard delete)."""
    current_task = await get_task(task_id)
    if not current_task or not current_task.data:
        raise HTTPException(status_code=404, detail="Task not found")
    before = current_task.data

    if user_id:
        await record_history(
            task_id=task_id,
            action="deleted",
            created_by=user_id,
            title=before.get("title"),
            metadata=[],  # keep small; you can include a few key fields if desired
            actor_display=actor_display,
        )

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
    org_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    supabase = get_supabase_client()
    query = supabase.from_("task_card_view").select("*").eq("is_subtask", False)

    if search:
        query = query.ilike("title", f"%{search}%")
    if status:
        query = query.eq("status", status)
    if org_id:
        query = query.eq("org_id", org_id)

    query = query.order(sort_by, desc=(sort_order.lower() == "desc"))
    result = query.range(offset, offset + limit - 1).execute()
    return result.data or []

async def get_tasks_for_project(
    project_id: str,
    search: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "title",
    sort_order: str = "asc",
    status: Optional[str] = None,
    org_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    supabase = get_supabase_client()
    query = supabase.from_("task_card_view").select("*").eq("project_id", project_id).eq("is_subtask", False)

    if search:
        query = query.ilike("title", f"%{search}%")
    if status:
        query = query.eq("status", status)
    if org_id:
        query = query.eq("org_id", org_id)

    query = query.order(sort_by, desc=(sort_order.lower() == "desc"))
    result = query.range(offset, offset + limit - 1).execute()
    return result.data or []

async def add_subtask(task_id: str, subtask_id: str, user_id: Optional[str] = None, actor_display: Optional[str] = None) -> Dict[str, Any]:
    task_res = await get_task(task_id)
    if not task_res or not task_res.data:
        raise HTTPException(status_code=404, detail="Parent task not found")

    before = task_res.data
    existing = before.get("sub_tasks") or []
    if subtask_id in existing:
        return task_res  # no-op

    updated = existing + [subtask_id]

    # Log explicit event
    if user_id:
        await record_history(
            task_id=task_id,
            action="subtask_added",
            created_by=user_id,
            title=before.get("title"),
            metadata={"subtask_id": subtask_id},
            actor_display=actor_display,
        )

    await update_task(subtask_id, {"is_subtask": True}, user_id, suppress_history=True, actor_display=actor_display)

    # Persist, suppress generic 'updated' history
    return await update_task(task_id, {"sub_tasks": updated}, user_id, suppress_history=True, actor_display=actor_display)

async def remove_subtask(task_id: str, subtask_id: str, user_id: Optional[str] = None, actor_display: Optional[str] = None) -> Dict[str, Any]:
    task_res = await get_task(task_id)
    if not task_res or not task_res.data:
        raise HTTPException(status_code=404, detail="Parent task not found")

    before = task_res.data
    existing = before.get("sub_tasks") or []
    if subtask_id not in existing:
        return task_res  # no-op

    updated = [sid for sid in existing if sid != subtask_id]

    if user_id:
        await record_history(
            task_id=task_id,
            action="subtask_removed",
            created_by=user_id,
            title=before.get("title"),
            metadata={"subtask_id": subtask_id},
            actor_display=actor_display,
        )

    await update_task(subtask_id, {"is_subtask": False}, user_id, suppress_history=True, actor_display=actor_display)

    return await update_task(task_id, {"sub_tasks": updated}, user_id, suppress_history=True, actor_display=actor_display)


async def add_dependency(
    task_id: str,
    dependency_id: str,
    user_id: Optional[str] = None,
    actor_display: Optional[str] = None
) -> Dict[str, Any]:
    task_res = await get_task(task_id)
    if not task_res or not task_res.data:
        raise HTTPException(status_code=404, detail="Parent task not found")

    before = task_res.data
    existing: list[str] = before.get("dependencies") or []
    if dependency_id in existing:
        return task_res  # no-op

    updated = existing + [dependency_id]

    if user_id:
        await record_history(
            task_id=task_id,
            action="dependency_added",
            created_by=user_id,
            title=before.get("title"),
            metadata={"dependency_id": dependency_id},
            actor_display=actor_display,
        )

    return await update_task(
        task_id,
        {"dependencies": updated},
        user_id,
        suppress_history=True,
        actor_display=actor_display,
    )


async def remove_dependency(
    task_id: str,
    dependency_id: str,
    user_id: Optional[str] = None,
    actor_display: Optional[str] = None
) -> Dict[str, Any]:
    task_res = await get_task(task_id)
    if not task_res or not task_res.data:
        raise HTTPException(status_code=404, detail="Parent task not found")

    before = task_res.data
    existing: list[str] = before.get("dependencies") or []
    if dependency_id not in existing:
        return task_res  # no-op

    updated = [d for d in existing if d != dependency_id]

    if user_id:
        await record_history(
            task_id=task_id,
            action="dependency_removed",
            created_by=user_id,
            title=before.get("title"),
            metadata={"dependency_id": dependency_id},
            actor_display=actor_display,
        )

    return await update_task(
        task_id,
        {"dependencies": updated},
        user_id,
        suppress_history=True,
        actor_display=actor_display,
    )