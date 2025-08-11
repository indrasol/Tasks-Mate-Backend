import datetime
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation


async def _generate_sequential_comment_id() -> str:
    """Generate the next sequential comment ID in the format 'C00001'."""
    supabase = get_supabase_client()

    def op():
        return (
            supabase
            .from_("task_comments")
            .select("comment_id")
            .order("comment_id", desc=True)
            .limit(1)
            .execute()
        )

    res = await safe_supabase_operation(op, "Failed to fetch last comment id")
    last_id: str | None = None
    if res and res.data:
        last_id = res.data[0].get("comment_id")

    last_num = 0
    if last_id and isinstance(last_id, str) and last_id.startswith("C"):
        try:
            last_num = int(last_id[1:])
        except ValueError:
            last_num = 0

    next_num = last_num + 1
    # Pad with 5 digits (C00001, C00010, etc.)
    return f"C{next_num:05d}"

async def create_task_comment(data: dict):
    # Ensure we always have correct timestamps if not provided
    if "created_at" not in data:
        data["created_at"] = datetime.datetime.utcnow().isoformat()

    # Generate comment_id if missing
    if not data.get("comment_id"):
        data["comment_id"] = await _generate_sequential_comment_id()

    # Some databases may still expect the legacy 'comment' column
    if data.get("content") and not data.get("comment"):
        data["comment"] = data["content"]

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
    # Stamp updated_at automatically if not provided
    if "updated_at" not in data:
        data["updated_at"] = datetime.datetime.utcnow().isoformat()
    supabase = get_supabase_client()
    def op():
        return supabase.from_("task_comments").update(data).eq("comment_id", comment_id).execute()
    return await safe_supabase_operation(op, "Failed to update task comment")

async def delete_task_comment(comment_id: str, _audit: dict | None = None):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("task_comments").delete().eq("comment_id", comment_id).execute()
    return await safe_supabase_operation(op, "Failed to delete task comment")

async def get_comments_for_task(task_id, search=None, limit=20, offset=0, sort_by="created_at", sort_order="asc"):
    supabase = get_supabase_client()
    query = supabase.from_("task_comments").select("*").eq("task_id", task_id)
    if search:
        # The column that stores the actual text body is `content`
        query = query.ilike("content", f"%{search}%")
    query = query.order(sort_by, desc=(sort_order == "desc"))
    result = query.range(offset, offset + limit - 1).execute()
    return result.data