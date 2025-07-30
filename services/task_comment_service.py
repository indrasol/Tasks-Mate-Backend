from core.db.supabase_db import get_supabase_client, safe_supabase_operation

async def create_task_comment(data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("task_comments").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to create task comment")

async def get_task_comment(comment_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("task_comments").select("*").eq("comment_id", comment_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch task comment")

async def update_task_comment(comment_id: str, data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("task_comments").update(data).eq("comment_id", comment_id).execute()
    return await safe_supabase_operation(op, "Failed to update task comment")

async def delete_task_comment(comment_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("task_comments").delete().eq("comment_id", comment_id).execute()
    return await safe_supabase_operation(op, "Failed to delete task comment")