from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from app.services.utils import inject_audit_fields

from app.utils.logger import get_logger

logger = get_logger()

import datetime
from fastapi import HTTPException

async def check_organization_member_exists(data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("organization_members").select("user_id").eq("org_id", data["org_id"]).eq("email", data["email"]).eq("is_active", True).limit(1).execute()
    res = await safe_supabase_operation(op, "Failed to check organization member exists")
    if res.data:
        raise HTTPException(400, detail="User is already a member of this organisation")

async def create_organization_member(data: dict):
    supabase = get_supabase_client()
    # Ensure invited_at timestamp
    now_iso = datetime.datetime.utcnow().isoformat()
    data.setdefault("invited_at", now_iso)
    # Auto-accept for owners (initial creator) if not provided
    if data.get("role") == "owner":
        data.setdefault("accepted_at", now_iso)

    await check_organization_member_exists(data)

    def op():
        return supabase.from_("organization_members").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to create organization member")

async def get_organization_member(user_id: str, org_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("organization_members").select("*").eq("user_id", user_id).eq("org_id", org_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch organization member")

async def update_organization_member(user_id: str, org_id: str, data: dict):
    supabase = get_supabase_client()
    def op():
        # data = inject_audit_fields(data,None,"update")
        return supabase.from_("organization_members").update(data).eq("user_id", user_id).eq("org_id", org_id).execute()
    return await safe_supabase_operation(op, "Failed to update organization member")

async def delete_organization_member(user_id: str, org_id: str, data:dict):
    supabase = get_supabase_client()
    def op():
        # data = inject_audit_fields(data,None,"delete")
        return supabase.from_("organization_members").delete().eq("user_id", user_id).eq("org_id", org_id).execute()
    return await safe_supabase_operation(op, "Failed to delete organization member")

async def get_members_for_org(org_id, search=None, limit=20, offset=0, sort_by="updated_at", sort_order="asc", role=None, is_active=None):
    supabase = get_supabase_client()
    # logger.info("Fetching members for org_id=%s", org_id)
    query = supabase.from_("organization_members").select("*").eq("org_id", org_id).eq("is_active", True)
    # if search:
    #     query = query.ilike("designation", f"%{search}%")
    if role:
        query = query.eq("role", role)
    # if is_active is not None:
    #     query = query.eq("is_active", is_active)
    query = query.order(sort_by, desc=(sort_order == "desc"))
    result = query.range(offset, offset + limit - 1).execute()
    return result.data