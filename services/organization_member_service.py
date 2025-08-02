from core.db.supabase_db import get_supabase_client, safe_supabase_operation
from services.utils import inject_audit_fields

from utils.logger import get_logger

logger = get_logger()

async def create_organization_member(data: dict):
    supabase = get_supabase_client()
    def op():
        # data = inject_audit_fields(data,None,"create")
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

async def delete_organization_member(user_id: str, org_id: str):
    supabase = get_supabase_client()
    def op():
        # data = inject_audit_fields(data,None,"delete")
        return supabase.from_("organization_members").delete().eq("user_id", user_id).eq("org_id", org_id).execute()
    return await safe_supabase_operation(op, "Failed to delete organization member")

async def get_members_for_org(org_id, search=None, limit=20, offset=0, sort_by="updated_at", sort_order="asc", role=None, is_active=None):
    supabase = get_supabase_client()
    query = supabase.from_("organization_members").select("*").eq("org_id", org_id)
    # if search:
    #     query = query.ilike("designation", f"%{search}%")
    if role:
        query = query.eq("role", role)
    if is_active is not None:
        query = query.eq("is_active", is_active)
    query = query.order(sort_by, desc=(sort_order == "desc"))
    result = query.range(offset, offset + limit - 1).execute()

    logger.info(query)
    logger.info(result.data)
    return result.data