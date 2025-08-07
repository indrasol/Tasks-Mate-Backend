from typing import List, Optional
from app.core.db.supabase_db import get_supabase_client as supabase_client, safe_supabase_operation
from app.models.schemas.project_stats import ProjectStatsInDB

async def get_project_stats(project_id: str) -> Optional[ProjectStatsInDB]:
    """Fetch statistics for a single project from `project_stats_view`."""
    supabase = supabase_client()

    def op():
        return (
            supabase.from_("project_stats_view")
            .select("*")
            .eq("project_id", project_id)
            .single()
            .execute()
        )

    result = await safe_supabase_operation(op, "Failed to fetch project stats")
    if result and result.data:
        return ProjectStatsInDB(**result.data)
    return None

async def get_all_project_stats() -> List[ProjectStatsInDB]:
    """Get stats for all projects"""
    supabase = supabase_client()

    def op():
        return supabase.from_("project_stats_view").select("*").execute()

    result = await safe_supabase_operation(op, "Failed to fetch all project stats")
    if not result or not result.data:
        return []
    return [ProjectStatsInDB(**item) for item in result.data]

async def get_organization_project_stats(org_id: str) -> List[ProjectStatsInDB]:
    """Get stats for all projects in an organization"""
    supabase = supabase_client()

    def op():
        return supabase.from_("project_stats_view").select("*").eq("org_id", org_id).execute()

    result = await safe_supabase_operation(op, "Failed to fetch organization project stats")
    if not result or not result.data:
        return []
    return [ProjectStatsInDB(**item) for item in result.data] 