from typing import Optional
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from fastapi import HTTPException


async def _generate_sequential_org_invite_id() -> str:
    """Generate the next sequential organization ID in the format 'O0001'.
    The numeric portion is strictly increasing even if organizations are
    deleted, as we always look at the current maximum and increment it.
    """
    supabase = get_supabase_client()

    def op():
        # Because the numeric part is zero-padded, ordering by the full string
        # gives us the highest numeric value as well.
        return (
            supabase
            .from_("organization_invites")
            .select("id")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )

    res = await safe_supabase_operation(op, "Failed to fetch last organization id")
    last_id: Optional[str] = None
    if res and res.data:
        last_id = res.data[0]["id"]

    last_num = 0
    if last_id and isinstance(last_id, str) and last_id.startswith("I"):
        try:
            last_num = int(last_id[1:])
        except ValueError:
            last_num = 0

    next_num = last_num + 1
    # Pad with at least 4 digits (O0001, O0010, etc.) but grow automatically
    return f"I{next_num:04d}"

async def check_organization_member_exists(data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("organization_members").select("user_id").eq("org_id", data["org_id"]).ilike("email", data["email"]).eq("is_active", True).limit(1).execute()
    res = await safe_supabase_operation(op, "Failed to check organization member exists")
    if res.data:
        raise HTTPException(400, detail="User is already a member of this organisation")

async def check_organization_invite_exists(data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("organization_invites").select("id").eq("org_id", data["org_id"]).ilike("email", data["email"]).eq("invite_status", "pending").limit(1).execute()
    res = await safe_supabase_operation(op, "Failed to check organization invite duplicate")
    if res.data:
        raise HTTPException(400, detail="An invite is already pending for this user")

async def create_organization_invite(data: dict):
    
    data['email'] = data['email'].lower()

    # Normalize designation to valid slug if provided
    if data.get("designation"):
        from app.services.organization_member_service import _resolve_designation_slug
        resolved = await _resolve_designation_slug(data["designation"])
        if not resolved:
            raise HTTPException(400, detail="Invalid designation provided")
        data["designation"] = resolved

    # A. already a member?
    await check_organization_member_exists(data)

    # B. duplicate pending invite?
    await check_organization_invite_exists(data)

    supabase = get_supabase_client()
    data["id"] = await _generate_sequential_org_invite_id()

    def op():        
        return supabase.from_("organization_invites").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to create organization invite")

async def get_organization_invite(invite_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("organization_invites").select("*").eq("id", invite_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch organization invite")

async def update_organization_invite(invite_id: str, data: dict):

    data['email'] = data['email'].lower()

    # Normalize designation to valid slug if provided
    if data.get("designation"):
        from app.services.organization_member_service import _resolve_designation_slug
        resolved = await _resolve_designation_slug(data["designation"])
        if not resolved:
            raise HTTPException(400, detail="Invalid designation provided")
        data["designation"] = resolved
    
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

    if email:
        email = email.lower()

    supabase = get_supabase_client()
    query = supabase.from_("organization_invites").select("*").eq("org_id", org_id)
    if search:
        query = query.ilike("email", f"%{search}%")
    if email:
        query = query.ilike("email", email)
    query = query.order(sort_by, desc=(sort_order == "desc"))
    result = query.range(offset, offset + limit - 1).execute()
    
    # Convert designation slugs back to display names for frontend
    invites = result.data or []
    for invite in invites:
        if invite.get("designation"):
            from app.services.organization_member_service import _resolve_slug_to_name
            display_name = await _resolve_slug_to_name(invite["designation"])
            if display_name:
                invite["designation"] = display_name
    
    return invites

async def get_invites_for_user(email:str):

    email = email.lower()

    supabase = get_supabase_client()
    query = supabase.from_("organization_invites").select("*").ilike("email", email)   
    result = query.execute()
    
    # Convert designation slugs back to display names for frontend
    invites = result.data or []
    for invite in invites:
        if invite.get("designation"):
            from app.services.organization_member_service import _resolve_slug_to_name
            display_name = await _resolve_slug_to_name(invite["designation"])
            if display_name:
                invite["designation"] = display_name
    
    return invites