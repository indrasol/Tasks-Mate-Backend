import datetime
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation



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


async def create_task(data: dict):


    data["task_id"] = await _generate_sequential_task_id()

    # Ensure we always have correct timestamps if not provided
    if "created_at" not in data:
        data["created_at"] = datetime.datetime.utcnow().isoformat()
    if data.get("assignee"):
        data["assignee"] = str(data["assignee"])
    # Serialize date fields if provided
    if data.get("start_date") and hasattr(data["start_date"], "isoformat"):
        data["start_date"] = data["start_date"].isoformat()
    if data.get("due_date") and hasattr(data["due_date"], "isoformat"):
        data["due_date"] = data["due_date"].isoformat()
    supabase = get_supabase_client()
    def op():
        return supabase.from_("tasks").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to create task")

async def get_task(task_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("tasks").select("*").eq("task_id", task_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch task")

async def update_task(task_id: str, data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("tasks").update(data).eq("task_id", task_id).execute()
    return await safe_supabase_operation(op, "Failed to update task")

async def delete_task(task_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("tasks").delete().eq("task_id", task_id).execute()
    return await safe_supabase_operation(op, "Failed to delete task")

async def get_all_tasks(search=None, limit=20, offset=0, sort_by="title", sort_order="asc", status=None):
    supabase = get_supabase_client()
    query = supabase.from_("task_card_view").select("*")
    if search:
        query = query.ilike("title", f"%{search}%")
    if status:
        query = query.eq("status", status)
    query = query.order(sort_by, desc=(sort_order == "desc"))
    result = query.range(offset, offset + limit - 1).execute()
    return result.data

async def get_tasks_for_project(project_id, search=None, limit=20, offset=0, sort_by="title", sort_order="asc", status=None):
    supabase = get_supabase_client()
    query = supabase.from_("task_card_view").select("*").eq("project_id", project_id)
    if search:
        query = query.ilike("title", f"%{search}%")
    if status:
        query = query.eq("status", status)
    query = query.order(sort_by, desc=(sort_order == "desc"))
    result = query.range(offset, offset + limit - 1).execute()
    return result.data