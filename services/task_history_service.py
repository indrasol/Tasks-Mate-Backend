from core.db.supabase_db import get_supabase_client, safe_supabase_operation

async def create_task_history(data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("tasks_history").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to create task history")

async def get_task_history(history_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("tasks_history").select("*").eq("history_id", history_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch task history")

async def update_task_history(history_id: str, data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("tasks_history").update(data).eq("history_id", history_id).execute()
    return await safe_supabase_operation(op, "Failed to update task history")

async def delete_task_history(history_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("tasks_history").delete().eq("history_id", history_id).execute()
    return await safe_supabase_operation(op, "Failed to delete task history")