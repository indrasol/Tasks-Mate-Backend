from typing import List
import uuid
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from app.models.schemas.project import ProjectCard

import datetime

async def _generate_sequential_project_id() -> str:
    """Generate the next sequential project ID in the format 'P00001'."""
    supabase = get_supabase_client()
    
    def op():
        return (
            supabase
            .from_("projects")
            .select("project_id")
            .order("project_id", desc=True)
            .limit(1)
            .execute()
        )

    res = await safe_supabase_operation(op, "Failed to fetch last project id")
    last_id: str | None = None
    if res and res.data:
        last_id = res.data[0]["project_id"]

    last_num = 0
    if last_id and isinstance(last_id, str) and last_id.startswith("P"):
        try:
            last_num = int(last_id[1:])
        except ValueError:
            last_num = 0

    next_num = last_num + 1
    # Pad with at least 5 digits (P00001, P00010, etc.)
    return f"P{next_num:05d}"


async def get_project_card(project_id: str):
    """Fetch a single ProjectCard entry from the materialized view for the given project."""
    supabase = get_supabase_client()
    def op():
        return (
            supabase
            .from_("project_card_view")
            .select("*")
            .eq("project_id", project_id)
            .single()
            .execute()
        )
    result = await safe_supabase_operation(op, "Failed to fetch project card")
    if result and result.data:
        return ProjectCard(**result.data)
    return None


async def create_project(data: dict):
    """Insert a new project and return the Supabase response."""
    supabase = get_supabase_client()

    # Generate the next sequential project_id
    project_id = await _generate_sequential_project_id()
    data["project_id"] = project_id

    # Ensure we always have correct timestamps if not provided
    if "created_at" not in data:
        data["created_at"] = datetime.datetime.utcnow().isoformat()

    def op():
        return supabase.from_("projects").insert(data).execute()

    return await safe_supabase_operation(op, "Failed to create project")

async def get_project(project_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("projects").select("*").eq("project_id", project_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch project")

async def update_project(project_id: str, data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("projects").update(data).eq("project_id", project_id).execute()
    return await safe_supabase_operation(op, "Failed to update project")

async def delete_project(project_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("projects").delete().eq("project_id", project_id).execute()
    return await safe_supabase_operation(op, "Failed to delete project")

# async def get_projects_for_user(user_id, org_id):
#     supabase = get_supabase_client()
#     result = supabase.from_("project_members").select("project_id").eq("user_id", user_id).execute()
#     project_ids = [row["project_id"] for row in result.data]
#     if not project_ids:
#         return []
#     # projects = supabase.from_("projects").select("*").in_("project_id", project_ids).eq("org_id", org_id).execute()
#     # return projects.data

#     """Get stats for a specific project"""
#     async def _get_stats():
#         result = supabase.from_("project_stats_view").select("*").in_("project_id", project_ids).execute()
#         if result:
#             return result
#         return None
    
#     result = await safe_supabase_operation(_get_stats)

#     if result:
#         return result
#     return None
#     # if isinstance(result, dict):
#     #     return List[ProjectCard(**result)]
#     # return None


async def get_projects_for_user(user_id, org_id):
    supabase = get_supabase_client()
    result = supabase.from_("project_members").select("project_id").eq("user_id", user_id).execute()
    project_ids = [row["project_id"] for row in result.data]
    if not project_ids:
        return []   

    stats_result = await safe_supabase_operation(lambda:supabase.from_("project_card_view").select("*").in_("project_id", project_ids).execute())

    # if stats_result:
    #     return [ProjectCard(**project) for project in stats_result]

    # return []

    if stats_result and stats_result.data:
        return [ProjectCard(**project) for project in stats_result.data]

    return []

