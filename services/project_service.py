from core.db.supabase_db import get_supabase_client, safe_supabase_operation

async def create_project(data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("projects").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to create project")

async def get_project(project_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("projects").select("*").eq("project_id", project_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch project")

async def update_project(project_id: str, data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("projects").update(data).eq("project_id", project_id).execute()
    return await safe_supabase_operation(op, "Failed to update project")

async def delete_project(project_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("projects").delete().eq("project_id", project_id).execute()
    return await safe_supabase_operation(op, "Failed to delete project")