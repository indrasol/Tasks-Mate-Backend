from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from fastapi import HTTPException


async def check_project_member_exists(data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_members").select("user_id").eq("project_id", data["project_id"]).eq("user_id",  data["user_id"]).limit(1).execute()
    res = await safe_supabase_operation(op, "Failed to check project member exists")
    if res.data:
        raise HTTPException(400, detail="User already belongs to this project")

async def create_project_member(data: dict):
    supabase = get_supabase_client()

    await check_project_member_exists(data)

    def op():
        return supabase.from_("project_members").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to create project member")

async def get_project_member(user_id: str, project_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_members").select("*").eq("user_id", user_id).eq("project_id", project_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch project member")

async def update_project_member(user_id: str, project_id: str, data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_members").update(data).eq("user_id", user_id).eq("project_id", project_id).execute()
    return await safe_supabase_operation(op, "Failed to update project member")

async def delete_project_member(user_id: str, project_id: str, metadata: dict | None = None):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_members").delete().eq("user_id", user_id).eq("project_id", project_id).execute()
    return await safe_supabase_operation(op, "Failed to delete project member")

async def get_members_for_project(project_id, search=None, limit=20, offset=0, sort_by="updated_at", sort_order="asc", role=None):
    supabase = get_supabase_client()
    query = supabase.from_("project_members").select("*").eq("project_id", project_id)
    # if search:
    #     query = query.ilike("user_name", f"%{search}%")
    if role:
        query = query.eq("role", role)
    query = query.order(sort_by, desc=(sort_order == "desc"))
    result = query.range(offset, offset + limit - 1).execute()
    return result.data