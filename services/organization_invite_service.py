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

async def get_invites_for_org(org_id, search=None, limit=20, offset=0, sort_by="email", sort_order="asc", email=None):
    supabase = get_supabase_client()
    query = supabase.from_("organization_invites").select("*").eq("org_id", org_id)
    if search:
        query = query.ilike("email", f"%{search}%")
    if email:
        query = query.eq("email", email)
    query = query.order(sort_by, desc=(sort_order == "desc"))
    result = query.range(offset, offset + limit - 1).execute()
    return result.data

async def get_invites_for_user(email:str):
    supabase = get_supabase_client()
    query = supabase.from_("organization_invites").select("*").eq("email", email)   
    result = query.execute()
    return result.data