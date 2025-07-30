from core.db.supabase_db import get_supabase_client, safe_supabase_operation

async def get_org_role(user_id: str, org_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("organization_members").select("role").eq("user_id", user_id).eq("org_id", org_id).single().execute()
    result = await safe_supabase_operation(op, "Failed to fetch org membership role")
    if result.data and result.data.get("role"):
        return result.data["role"]
    return None

async def get_project_role(user_id: str, project_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_members").select("role").eq("user_id", user_id).eq("project_id", project_id).single().execute()
    result = await safe_supabase_operation(op, "Failed to fetch project membership role")
    if result.data and result.data.get("role"):
        return result.data["role"]
    return None