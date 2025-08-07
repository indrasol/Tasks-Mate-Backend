from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.project_stats_service import get_project_stats, get_all_project_stats, get_organization_project_stats
from app.models.schemas.project_stats import ProjectStatsInDB
from app.services.auth_handler import verify_token
from app.services.rbac import get_project_role

router = APIRouter()

@router.get("/{project_id}/stats", response_model=ProjectStatsInDB, tags=["Project Stats"])
async def get_project_statistics(
    project_id: str,
    current_user: dict = Depends(verify_token)
):
    """Get statistics for a specific project"""
    # Check if user has access to the project
    user_role = await get_project_role(current_user["id"], project_id)
    if not user_role:
        raise HTTPException(status_code=403, detail="Access denied to this project")
    
    stats = await get_project_stats(project_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Project stats not found")
    
    return stats

@router.get("/stats/all", response_model=List[ProjectStatsInDB], tags=["Project Stats"])
async def get_all_projects_statistics(
    current_user: dict = Depends(verify_token)
):
    """Get statistics for all projects (admin only)"""
    # This endpoint could be restricted to admin users only
    # For now, allowing any authenticated user
    stats = await get_all_project_stats()
    return stats

@router.get("/stats/organization/{org_id}", response_model=List[ProjectStatsInDB], tags=["Project Stats"])
async def get_organization_projects_statistics(
    org_id: str,
    current_user: dict = Depends(verify_token)
):
    """Get statistics for all projects in an organization"""
    # Check if user has access to the organization
    from services.rbac import get_org_role
    user_role = await get_org_role(current_user["user_id"], org_id)
    if not user_role:
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    stats = await get_organization_project_stats(org_id)
    return stats 