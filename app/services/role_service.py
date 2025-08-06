from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation

async def create_role(data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("roles").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to create role")

async def get_role(role_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("roles").select("*").eq("role_id", role_id).limit(1).execute()
    return await safe_supabase_operation(op, "Failed to fetch role")


async def get_role_by_name(role_name: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("roles").select("*").eq("name", role_name).limit(1).execute()
    return await safe_supabase_operation(op, "Failed to fetch role by name")

async def update_role(role_id: str, data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("roles").update(data).eq("role_id", role_id).execute()
    return await safe_supabase_operation(op, "Failed to update role")

async def delete_role(role_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("roles").delete().eq("role_id", role_id).execute()
    return await safe_supabase_operation(op, "Failed to delete role")