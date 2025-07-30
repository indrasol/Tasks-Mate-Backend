from core.db.supabase_db import get_supabase_client, safe_supabase_operation

async def create_organization(data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("organizations").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to create organization")

async def get_organization(org_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("organizations").select("*").eq("org_id", org_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch organization")

async def update_organization(org_id: str, data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("organizations").update(data).eq("org_id", org_id).execute()
    return await safe_supabase_operation(op, "Failed to update organization")

async def delete_organization(org_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("organizations").delete().eq("org_id", org_id).execute()
    return await safe_supabase_operation(op, "Failed to delete organization")