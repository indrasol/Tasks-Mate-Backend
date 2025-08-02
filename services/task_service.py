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

async def get_all_tasks(search=None, limit=20, offset=0, sort_by="title", sort_order="asc", status=None):
    supabase = get_supabase_client()
    query = supabase.from_("tasks").select("*")
    if search:
        query = query.ilike("title", f"%{search}%")
    if status:
        query = query.eq("status", status)
    query = query.order(sort_by, desc=(sort_order == "desc"))
    result = query.range(offset, offset + limit - 1).execute()
    return result.data

async def get_tasks_for_project(project_id, search=None, limit=20, offset=0, sort_by="title", sort_order="asc", status=None):
    supabase = get_supabase_client()
    query = supabase.from_("tasks").select("*").eq("project_id", project_id)
    if search:
        query = query.ilike("title", f"%{search}%")
    if status:
        query = query.eq("status", status)
    query = query.order(sort_by, desc=(sort_order == "desc"))
    result = query.range(offset, offset + limit - 1).execute()
    return result.data