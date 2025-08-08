import datetime
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation

async def create_task_attachment(data: dict):

     # Ensure we always have correct timestamps if not provided
    if "created_at" not in data:
        data["created_at"] = datetime.datetime.utcnow().isoformat()
        
    supabase = get_supabase_client()
    def op():
        return supabase.from_("task_attachments").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to create task attachment")

async def get_task_attachment(attachment_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("task_attachments").select("*").eq("attachment_id", attachment_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch task attachment")

async def update_task_attachment(attachment_id: str, data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("task_attachments").update(data).eq("attachment_id", attachment_id).execute()
    return await safe_supabase_operation(op, "Failed to update task attachment")

async def delete_task_attachment(attachment_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("task_attachments").delete().eq("attachment_id", attachment_id).execute()
    return await safe_supabase_operation(op, "Failed to delete task attachment")