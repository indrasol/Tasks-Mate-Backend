import datetime
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from app.models.schemas.task_history import TaskHistoryInDB


async def _generate_sequential_history_id() -> str:
    """Generate the next sequential task ID in the format 'T000000001'."""
    supabase = get_supabase_client()
    
    def op():
        
        return (
            supabase
            .from_("tasks_history")
            .select("history_id")
            .order("history_id", desc=True)
            .limit(1)
            .execute()
        )

    res = await safe_supabase_operation(op, "Failed to fetch last project id")
    last_id: str | None = None
    if res and res.data:
        last_id = res.data[0]["history_id"]

    last_num = 0
    if last_id and isinstance(last_id, str) and last_id.startswith("H"):
        try:
            last_num = int(last_id[1:])
        except ValueError:
            last_num = 0

    next_num = last_num + 1
    # Pad with at least 5 digits (P00001, P00010, etc.)
    return f"H{next_num:10d}"


async def create_task_history(data: dict):

    data["history_id"] = await _generate_sequential_history_id()

     # Ensure we always have correct timestamps if not provided
    if "created_at" not in data:
        data["created_at"] = datetime.datetime.utcnow().isoformat()
        
    supabase = get_supabase_client()
    def op():
        return supabase.from_("tasks_history").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to create task history")

async def get_task_history(task_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("tasks_history").select("*").eq("task_id", task_id).execute()
    result = await safe_supabase_operation(op, "Failed to fetch task history")

    return [TaskHistoryInDB(**item) for item in result.data or []]
# async def update_task_history(history_id: str, data: dict):
#     supabase = get_supabase_client()
#     def op():
#         return supabase.from_("tasks_history").update(data).eq("history_id", history_id).execute()
#     return await safe_supabase_operation(op, "Failed to update task history")

# async def delete_task_history(history_id: str):
#     supabase = get_supabase_client()
#     def op():
#         return supabase.from_("tasks_history").delete().eq("history_id", history_id).execute()
#     return await safe_supabase_operation(op, "Failed to delete task history")