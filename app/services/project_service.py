from typing import List
from app.models.enums import RoleEnum
import uuid
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from app.models.schemas.project import ProjectCard

import datetime
from fastapi import HTTPException
import random  # NEW: needed for random ID generation


# ---------------------------------------------------------------------------
# Project ID generation
# ---------------------------------------------------------------------------


async def _generate_random_project_id() -> str:
    """Generate a random project ID with prefix 'P' and 6 digits, ensuring uniqueness."""

    supabase = get_supabase_client()
    digits = 5

    # Try a few times to avoid collisions (extremely unlikely)
    for _ in range(10):
        candidate = f"P{random.randint(0, 10**digits - 1):0{digits}d}"

        def op():
            return (
                supabase.from_("projects")
                .select("project_id")
                .eq("project_id", candidate)
                .limit(1)
                .execute()
            )

        res = await safe_supabase_operation(op, "Failed to verify project id uniqueness")
        if not res or not getattr(res, "data", None):
            return candidate

    # Fallback: use timestamp suffix (still reasonably unique)
    ts = int(datetime.datetime.utcnow().timestamp()) % (10 ** digits)
    return f"P{ts:0{digits}d}"


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


async def check_project_exists(data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("projects").select("project_id").eq("org_id", data["org_id"]).eq("name",  data["name"]).limit(1).execute()
    res = await safe_supabase_operation(op, "Failed to check project exists")
    if res.data:
        raise HTTPException(400, detail="A project with the same name already exists in this organisation")

async def create_project(data: dict):
    """Insert a new project and return the Supabase response."""
    supabase = get_supabase_client()

    await check_project_exists(data)

    # Generate a random project_id (P + 6 digits)
    project_id = await _generate_random_project_id()
    data["project_id"] = project_id

    # Ensure we always have correct timestamps if not provided
    if "created_at" not in data:
        data["created_at"] = datetime.datetime.utcnow().isoformat()

    # Remove owner_designation from the data before inserting into projects table
    # This is because it's not needed in the projects table (we store it in project_members)
    owner_designation = data.pop("owner_designation", None)

    # Serialize any date/datetime objects to ISO strings so Supabase JSON encoder can handle them
    for k, v in list(data.items()):
        if isinstance(v, (datetime.date, datetime.datetime)):
            data[k] = v.isoformat()

    def op():
        return supabase.from_("projects").insert(data).execute()

    return await safe_supabase_operation(op, "Failed to create project")

async def get_project(project_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("projects").select("*").eq("project_id", project_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch project")

async def _update_project_name_references(project_id: str, new_name: str):
    """
    Update project name references in linked tasks and trackers.
    
    This function is automatically called when a project name is updated and ensures
    that all linked entities (currently test_trackers) are kept in sync with the new name.
    
    Args:
        project_id: The project's unique identifier
        new_name: The updated project name
        
    Returns:
        None
    """
    supabase = get_supabase_client()
    
    # Note: Tasks table doesn't store project_name, only project_id which doesn't change
    # So we don't need to update tasks when project name changes
    
    # Update project name in test_trackers table
    try:
        def tracker_op():
            return supabase.from_("test_trackers") \
                .update({"project_name": new_name}) \
                .eq("project_id", project_id) \
                .execute()
        result = await safe_supabase_operation(tracker_op, "Failed to update project name in trackers")
        
        # Log how many trackers were updated
        count = len(result.data) if result and hasattr(result, 'data') else 0
        print(f"Updated project name to '{new_name}' in {count} test trackers for project {project_id}")
        
    except Exception as e:
        print(f"Error updating project name in trackers: {str(e)}")

async def update_project(project_id: str, data: dict):
    """
    Update a project and automatically cascade the name change to linked entities.
    
    When the project name is updated, this function automatically updates all references
    to the project name in related tables (like test_trackers) to maintain data consistency.
    
    Args:
        project_id: The project's unique identifier
        data: Dictionary of project fields to update
        
    Returns:
        The Supabase response from the update operation
    """
    supabase = get_supabase_client()
    
    # Check if project name is being updated
    update_name = False
    if "name" in data:
        # Get current project to compare
        current_project = await get_project(project_id)
        if current_project and current_project.data:
            if current_project.data.get("name") != data["name"]:
                update_name = True
                print(f"Project name change detected: '{current_project.data.get('name')}' → '{data['name']}'")
    
    # Ensure date/datetime values are JSON serializable
    for k, v in list(data.items()):
        if isinstance(v, (datetime.date, datetime.datetime)):
            data[k] = v.isoformat()
    
    # Update the project
    def op():
        return supabase.from_("projects").update(data).eq("project_id", project_id).execute()
    
    result = await safe_supabase_operation(op, "Failed to update project")
    
    # If project name was updated, update related entities
    if update_name and result and result.data:
        await _update_project_name_references(project_id, data["name"])
    
    return result

async def delete_project(project_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("projects").delete().eq("project_id", project_id).execute()
    return await safe_supabase_operation(op, "Failed to delete project")


async def get_all_org_projects(org_id: str):
    """Get all projects for an organization regardless of user membership."""
    supabase = get_supabase_client()
    
    def op():
        return supabase.from_("project_card_view").select("*").eq("org_id", org_id).execute()
    
    stats_result = await safe_supabase_operation(op, "Failed to fetch organization projects")
    
    if not stats_result or not stats_result.data:
        return []
    
    enriched: list[ProjectCard] = []
    for raw in stats_result.data:
        card = ProjectCard(**raw)
        # Fetch members for each project (owner + team list)
        mem_res = await safe_supabase_operation(
            lambda: supabase.from_("project_members").select("user_id,role").eq("project_id", card.project_id).execute(),
            "Failed to fetch project members",
        )
        if mem_res and mem_res.data:
            card.team_members = [m["user_id"] for m in mem_res.data]
            owner_row = next((m for m in mem_res.data if m.get("role") == RoleEnum.OWNER.value), None)
            if owner_row:
                card.owner = owner_row["user_id"]
        enriched.append(card)

    return enriched

async def get_projects_for_user(user_id, org_id):
    """Get only the projects where the user is a member."""
    supabase = get_supabase_client()
    result = supabase.from_("project_members").select("project_id").eq("user_id", user_id).execute()
    project_ids = [row["project_id"] for row in result.data]
    if not project_ids:
        return []   

    stats_result = await safe_supabase_operation(lambda:supabase.from_("project_card_view").select("*").in_("project_id", project_ids).eq("org_id", org_id).execute())


    if not stats_result or not stats_result.data:
        return []

    enriched: list[ProjectCard] = []
    for raw in stats_result.data:
        card = ProjectCard(**raw)
        # Fetch members for each project (owner + team list)
        mem_res = await safe_supabase_operation(
            lambda: supabase.from_("project_members").select("user_id,role").eq("project_id", card.project_id).execute(),
            "Failed to fetch project members",
        )
        if mem_res and mem_res.data:
            card.team_members = [m["user_id"] for m in mem_res.data]
            owner_row = next((m for m in mem_res.data if m.get("role") == RoleEnum.OWNER.value), None)
            if owner_row:
                card.owner = owner_row["user_id"]
        enriched.append(card)

    return enriched

