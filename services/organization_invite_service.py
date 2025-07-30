from core.db.supabase_db import get_supabase_client, safe_supabase_operation

async def create_organization_invite(data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("organization_invites").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to create organization invite")

async def get_organization_invite(invite_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("organization_invites").select("*").eq("id", invite_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch organization invite")

async def update_organization_invite(invite_id: str, data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("organization_invites").update(data).eq("id", invite_id).execute()
    return await safe_supabase_operation(op, "Failed to update organization invite")

async def delete_organization_invite(invite_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("organization_invites").delete().eq("id", invite_id).execute()
    return await safe_supabase_operation(op, "Failed to delete organization invite")