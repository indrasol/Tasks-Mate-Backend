from typing import List, Optional
from app.core.db.supabase_db import get_supabase_client as supabase_client, safe_supabase_operation
from app.models.schemas.project_stats import ProjectStatsInDB

async def get_project_stats(project_id: str) -> Optional[ProjectStatsInDB]:
    """Get stats for a specific project"""
    async def _get_stats():
        result = supabase_client.table("project_stats_view").select("*").eq("project_id", project_id).execute()
        if result.data:
            return result.data[0]
        return None
    
    data = await safe_supabase_operation(_get_stats)
    if data:
        return ProjectStatsInDB(**data)
    return None

async def get_all_project_stats() -> List[ProjectStatsInDB]:
    """Get stats for all projects"""
    async def _get_all_stats():
        result = supabase_client.table("project_stats_view").select("*").execute()
        return result.data
    
    data = await safe_supabase_operation(_get_all_stats)
    return [ProjectStatsInDB(**item) for item in data]

async def get_organization_project_stats(org_id: str) -> List[ProjectStatsInDB]:
    """Get stats for all projects in an organization"""
    async def _get_org_stats():
        result = supabase_client.table("project_stats_view").select("*").eq("org_id", org_id).execute()
        return result.data
    
    data = await safe_supabase_operation(_get_org_stats)
    return [ProjectStatsInDB(**item) for item in data] 