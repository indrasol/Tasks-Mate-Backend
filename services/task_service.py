from core.db.supabase_db import get_supabase_client, safe_supabase_operation

async def create_task(data: dict):
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