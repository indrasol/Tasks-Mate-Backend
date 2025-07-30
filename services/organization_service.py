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

async def get_organizations_for_user(user_id, email=None):
    supabase = get_supabase_client()
    # Get orgs where user is a member
    member_result = supabase.from_("organization_members").select("org_id").eq("user_id", user_id).execute()
    member_org_ids = set(row["org_id"] for row in member_result.data or [])
    # Get orgs where user is invited (by email)
    invite_org_ids = set()
    if email:
        invite_result = supabase.from_("organization_invites").select("org_id").eq("email", email).execute()
        invite_org_ids = set(row["org_id"] for row in invite_result.data or [])
    # Only show invite if not already a member
    only_invite_org_ids = invite_org_ids - member_org_ids
    all_org_ids = member_org_ids | only_invite_org_ids
    if not all_org_ids:
        return []
    orgs = supabase.from_("organizations").select("*").in_("org_id", list(all_org_ids)).execute()
    # Annotate each org with status
    for org in orgs.data:
        if org["org_id"] in member_org_ids:
            org["access_status"] = "member"
        else:
            org["access_status"] = "invite"
    return orgs.data