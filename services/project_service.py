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

async def get_projects_for_user(user_id):
    supabase = get_supabase_client()
    result = supabase.from_("project_members").select("project_id").eq("user_id", user_id).execute()
    project_ids = [row["project_id"] for row in result.data]
    if not project_ids:
        return []
    projects = supabase.from_("projects").select("*").in_("project_id", project_ids).execute()
    return projects.data