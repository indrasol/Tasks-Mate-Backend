import datetime
from typing import Dict, Any, List, Optional
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from fastapi import HTTPException
import random

async def _generate_tracker_id() -> str:
    """Generate a unique tracker ID with prefix 'TR-' and 4 digits."""
    supabase = get_supabase_client()
    digits = 4
    for _ in range(10):
        candidate = f"TR-{random.randint(0, 10**digits - 1):0{digits}d}"
        def op():
            return supabase.from_("test_trackers").select("tracker_id").eq("tracker_id", candidate).limit(1).execute()
        res = await safe_supabase_operation(op, "Failed to verify tracker id uniqueness")
        if not res or not getattr(res, "data", None):
            return candidate
    # Fallback: time-based suffix to reduce collision risk
    ts = int(datetime.datetime.utcnow().timestamp()) % (10**digits)
    return f"TR-{ts:0{digits}d}"

async def create_tracker(data: dict) -> Dict[str, Any]:
    """Create a new test tracker."""
    tracker_id = await _generate_tracker_id()
    data["tracker_id"] = tracker_id

    # Ensure we always have correct timestamps if not provided
    created_at = datetime.datetime.utcnow().isoformat()
    if "created_at" not in data:
        data["created_at"] = created_at
    if "updated_at" not in data:
        data["updated_at"] = created_at
    
    # Make sure creator_id is a string
    if data.get("creator_id"):
        data["creator_id"] = str(data["creator_id"])
    
    # Insert the tracker
    supabase = get_supabase_client()
    def op():
        return supabase.from_("test_trackers").insert(data).execute()
    
    result = await safe_supabase_operation(op, "Failed to create test tracker")
    return result

async def get_tracker(tracker_id: str):
    """Get a specific test tracker by ID."""
    supabase = get_supabase_client()
    def op():
        return supabase.from_("test_trackers").select("*").eq("tracker_id", tracker_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch test tracker")

async def update_tracker(tracker_id: str, data: dict):
    """Update an existing test tracker."""
    # Ensure updated_at is set
    data["updated_at"] = datetime.datetime.utcnow().isoformat()
    
    supabase = get_supabase_client()
    def op():
        return supabase.from_("test_trackers").update(data).eq("tracker_id", tracker_id).execute()
    return await safe_supabase_operation(op, "Failed to update test tracker")

async def delete_tracker(tracker_id: str, delete_reason: Optional[str] = None):
    """Soft delete a test tracker by setting deleted_at and delete_reason."""
    supabase = get_supabase_client()
    data = {
        "deleted_at": datetime.datetime.utcnow().isoformat(),
        "is_active": False
    }
    if delete_reason:
        data["delete_reason"] = delete_reason
    
    def op():
        return supabase.from_("test_trackers").update(data).eq("tracker_id", tracker_id).execute()
    return await safe_supabase_operation(op, "Failed to delete test tracker")

async def hard_delete_tracker(tracker_id: str):
    """Hard delete a test tracker (remove from database)."""
    supabase = get_supabase_client()
    def op():
        return supabase.from_("test_trackers").delete().eq("tracker_id", tracker_id).execute()
    return await safe_supabase_operation(op, "Failed to delete test tracker")

async def get_trackers_for_org(
    org_id: str,
    search: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    status: Optional[str] = None,
    project_id: Optional[str] = None,
    creator_id: Optional[str] = None,
    priority: Optional[str] = None
):
    """Get all test trackers for an organization with optional filtering."""
    supabase = get_supabase_client()
    
    query = supabase.from_("test_trackers").select("*").eq("org_id", org_id).is_("deleted_at", "null")
    
    # Apply filters if provided
    if status:
        query = query.eq("status", status)
    if project_id:
        query = query.eq("project_id", project_id)
    if creator_id:
        query = query.eq("creator_id", creator_id)
    if priority:
        query = query.eq("priority", priority)
    if search:
        query = query.or_(f"name.ilike.%{search}%,description.ilike.%{search}%,tracker_id.ilike.%{search}%")
    
    # Apply sorting
    if sort_order.lower() == "desc":
        query = query.order(sort_by, desc=True)
    else:
        query = query.order(sort_by)
    
    # Apply pagination
    query = query.range(offset, offset + limit - 1)
    
    def op():
        return query.execute()
    
    result = await safe_supabase_operation(op, "Failed to fetch test trackers")
    return result
