from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.v1.routes.organizations.org_rbac import org_rbac
# from app.api.v1.routes.projects.proj_rbac import project_rbac
from app.models.schemas.tracker import TrackerCreate, TrackerStatsView, TrackerUpdate, TrackerInDB, TrackerCardView
from app.services.tracker_service import (
    create_tracker,
    get_tracker,
    get_tracker_stats,
    update_tracker, 
    delete_tracker,
    hard_delete_tracker,
    get_trackers_for_org
)
from app.services.auth_handler import verify_token
from app.services.rbac import get_org_role, get_project_role

router = APIRouter()

@router.post("", response_model=TrackerInDB)
async def create_tracker_route(tracker: TrackerCreate, user=Depends(verify_token)):
    """Create a new test tracker."""

    org_role = await get_org_role(user["id"], tracker.org_id)
    if not org_role:
        raise HTTPException(status_code=403, detail="Not authorized to access this tracker")
    

    # Check if user has access to the project
    # project_role = await get_project_role(user["id"], tracker.project_id)
    # if not project_role:
    #     raise HTTPException(status_code=403, detail="Not authorized to create trackers for this project")
    
    # Add created_by to data
    data = {**tracker.model_dump(), "creator_name": user["username"],"creator_id":user["id"]}
    result = await create_tracker(data)
    
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create test tracker")
    
    return result.data[0]

@router.get("/{org_id}", response_model=List[TrackerCardView])
async def list_trackers(
    org_id: str,
    user=Depends(verify_token),
    org_role=Depends(org_rbac),
    search: Optional[str] = Query(None),
    limit: int = Query(100000, ge=1),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    status: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    creator_id: Optional[str] = Query(None),
    priority: Optional[str] = Query(None)
):
    """Get all test trackers for an organization with optional filtering."""
    if not org_role:
        raise HTTPException(status_code=403, detail="Not authorized to access this organization")
    
    result = await get_trackers_for_org(
        org_id=org_id,
        search=search,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
        status=status,
        project_id=project_id,
        creator_id=creator_id,
        priority=priority
    )
    
    return result.data

@router.get("/detail/{tracker_id}", response_model=TrackerStatsView)
async def get_tracker_route(tracker_id: str, user=Depends(verify_token)):
    """Get details of a specific test tracker."""
    result = await get_tracker_stats(tracker_id)
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Tracker not found")

    org_role = await get_org_role(user["id"], result.data["org_id"])
    if not org_role:
        raise HTTPException(status_code=403, detail="Not authorized to access this tracker")
    
    # Check if user has access to the project
    # project_role = await get_project_role(user["id"], result.data["project_id"])
    # if not project_role:
    #     raise HTTPException(status_code=403, detail="Not authorized to access this tracker")
    
    
    return result.data

@router.put("/{tracker_id}", response_model=TrackerInDB)
async def update_tracker_route(tracker_id: str, tracker: TrackerUpdate, user=Depends(verify_token)):
    """Update an existing test tracker."""
    # First get the existing tracker to check permissions
    existing_tracker = await get_tracker(tracker_id)
    
    if not existing_tracker.data:
        raise HTTPException(status_code=404, detail="Tracker not found")
    
    # Check if user has access to the project
    # project_role = await get_project_role(user["id"], existing_tracker.data["project_id"])
    # if not project_role:
    #     raise HTTPException(status_code=403, detail="Not authorized to update this tracker")
    
    # If project_id is being updated, check if user has access to the new project
    # if tracker.project_id and tracker.project_id != existing_tracker.data["project_id"]:
    #     new_project_role = await get_project_role(user["id"], tracker.project_id)
    #     if not new_project_role:
    #         raise HTTPException(status_code=403, detail="Not authorized to move tracker to the specified project")
    
    # Add updated_by to data
    data = {**tracker.model_dump(exclude_unset=True), "updated_by": user["username"]}
    result = await update_tracker(tracker_id, data)
    
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update test tracker")
    
    return result.data[0]

@router.delete("/{tracker_id}")
async def delete_tracker_route(
    tracker_id: str, 
    user=Depends(verify_token),
    hard_delete: bool = Query(False, description="If true, permanently removes the tracker from the database"),
    delete_reason: Optional[str] = Query(None, description="Reason for deletion")
):
    """Delete a test tracker (soft delete by default, hard delete if specified)."""
    # First get the existing tracker to check permissions
    existing_tracker = await get_tracker(tracker_id)
    
    if not existing_tracker.data:
        raise HTTPException(status_code=404, detail="Tracker not found")

    org_role = await get_org_role(user["id"], existing_tracker.data["org_id"])
    if not org_role:
        raise HTTPException(status_code=403, detail="Not authorized to access this tracker")
    
    
    # Check if user has access to the project
    # project_role = await get_project_role(user["id"], existing_tracker.data["project_id"])
    # if not project_role or project_role not in ["owner", "admin"]:
    #     raise HTTPException(status_code=403, detail="Not authorized to delete this tracker")
    
    if hard_delete:
        await hard_delete_tracker(tracker_id)
    else:
        await delete_tracker(tracker_id, delete_reason)
    
    return {"ok": True, "message": "Tracker deleted successfully"}
