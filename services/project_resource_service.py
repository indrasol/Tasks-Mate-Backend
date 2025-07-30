from core.db.supabase_db import get_supabase_client, safe_supabase_operation

async def create_project_resource(data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_resources").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to create project resource")

async def get_project_resource(resource_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_resources").select("*").eq("resource_id", resource_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch project resource")

async def update_project_resource(resource_id: str, data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_resources").update(data).eq("resource_id", resource_id).execute()
    return await safe_supabase_operation(op, "Failed to update project resource")

async def delete_project_resource(resource_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_resources").delete().eq("resource_id", resource_id).execute()
    return await safe_supabase_operation(op, "Failed to delete project resource")