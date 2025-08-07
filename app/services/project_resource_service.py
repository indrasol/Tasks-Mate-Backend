from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation

import datetime

async def _generate_sequential_resource_id() -> str:
    """Generate next sequential id like 'RE0001'"""
    supabase = get_supabase_client()
    def op():
        return (
            supabase.from_("project_resources")
            .select("resource_id")
            .order("resource_id", desc=True)
            .limit(1)
            .execute()
        )
    res = await safe_supabase_operation(op, "Failed to fetch last resource id")
    last = res.data[0]["resource_id"] if res and res.data else None
    last_num = 0
    if last and isinstance(last, str) and last.startswith("RE"):
        try:
            last_num = int(last[2:])
        except ValueError:
            last_num = 0
    return f"RE{last_num+1:04d}"

async def create_project_resource(data: dict):
    # Map flexible keys
    if "name" in data and "resource_name" not in data:
        data["resource_name"] = data.pop("name")
    if "url" in data and "resource_url" not in data:
        data["resource_url"] = data.pop("url")

    # Fetch project_name if not provided
    if "project_id" in data and "project_name" not in data:
        try:
            proj_sb = get_supabase_client()
            proj_res = proj_sb.from_("projects").select("name").eq("project_id", data["project_id"]).single().execute()
            if proj_res and proj_res.data and proj_res.data.get("name"):
                data["project_name"] = proj_res.data["name"]
        except Exception:
            pass

    if "resource_id" not in data:
        data["resource_id"] = await _generate_sequential_resource_id()

    if "created_at" not in data:
        data["created_at"] = datetime.datetime.utcnow().isoformat()

    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_resources").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to create project resource")

async def get_project_resource(resource_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_resources").select("*").eq("resource_id", resource_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch project resource")

async def update_project_resource(resource_id: str, data: dict):
    if "name" in data and "resource_name" not in data:
        data["resource_name"] = data.pop("name")
    if "url" in data and "resource_url" not in data:
        data["resource_url"] = data.pop("url")
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_resources").update(data).eq("resource_id", resource_id).execute()
    return await safe_supabase_operation(op, "Failed to update project resource")

async def delete_project_resource(resource_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_resources").delete().eq("resource_id", resource_id).execute()
    return await safe_supabase_operation(op, "Failed to delete project resource")

async def get_resources_for_project(project_id, search=None, limit=20, offset=0, sort_by="resource_type", sort_order="asc", resource_type=None):
    supabase = get_supabase_client()
    query = supabase.from_("project_resources").select("*").eq("project_id", project_id)
    if search:
        query = query.ilike("resource_type", f"%{search}%")
    if resource_type:
        query = query.eq("resource_type", resource_type)
    query = query.order(sort_by, desc=(sort_order == "desc"))
    result = query.range(offset, offset + limit - 1).execute()
    return result.data