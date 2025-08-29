from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from app.services.role_service import get_role, get_role_by_name

async def get_org_role(user_id: str, org_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("organization_members").select("role").eq("user_id", user_id).eq("org_id", org_id).limit(1).execute()
    result = await safe_supabase_operation(op, "Failed to fetch org membership role")
    if result.data and len(result.data) > 0:
        role_name = result.data[0].get("role")
        # Try resolving to human-readable role name
        # role_details = await get_role(role_id)
        # if role_details and role_details.data and role_details.data.get("name"):
        #     return role_details.data.get("name").lower()
        # Fallback to UUID/id string
        return role_name
    return None

async def get_project_role(user_id: str, project_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_members").select("role").eq("user_id", user_id).eq("project_id", project_id).limit(1).execute()
    result = await safe_supabase_operation(op, "Failed to fetch project membership role")
    if result.data and len(result.data) > 0:
        role_name = result.data[0].get("role")
        # Try resolving to human-readable role name
        # role_details = await get_role(role_id)
        # if role_details and role_details.data and role_details.data.get("name"):
        #     return role_details.data.get("name").lower()
        return role_name
    return None