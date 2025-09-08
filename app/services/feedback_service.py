from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
import datetime
import uuid

async def insert_feedback(data: dict, user: dict):
    data["id"] = str(uuid.uuid4())
    data["submitted_by"] = user["id"]
    data["submitted_at"] = datetime.datetime.utcnow().isoformat()
    supabase = get_supabase_client()
    def op():
        return supabase.from_("feedback").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to insert feedback")

async def get_feedback(user: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("feedback").select("*").execute()
    response = await safe_supabase_operation(op, "Failed to fetch feedback")
    # response probably looks like: {"data": [...], "error": None, ...}

    return response.data if response and response.data else []

async def get_feedback_by_user(user_id: str):
    supabase = get_supabase_client()
    def op(user_id: str):
        return supabase.from_("feedback").select("*").eq("submitted_by", user_id).execute()
    response = await safe_supabase_operation(op, "Failed to fetch feedback")
    # response probably looks like: {"data": [...], "error": None, ...}

    return response.data if response and response.data else []

async def delete_feedback(feedback_id: str):
    supabase = get_supabase_client()
    def op(feedback_id: str):
        return supabase.from_("feedback").delete().eq("id", feedback_id).execute()
    return await safe_supabase_operation(op, "Failed to delete feedback")
