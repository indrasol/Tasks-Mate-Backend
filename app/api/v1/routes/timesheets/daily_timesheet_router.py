from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from app.services.auth_handler import verify_token
from app.api.v1.routes.organizations.org_rbac import org_rbac
from app.models.schemas.daily_timesheet import (
    DailyTimesheetCreate,
    DailyTimesheetUpdate,
    DailyTimesheetInDB,
    DailyTimesheetWithDetails,
    DailyTimesheetFilters,
    DailyTimesheetBulkUpdate,
    DailyTimesheetResponse,
    DailyTimesheetListResponse
)
from app.services.daily_timesheet_service import (
    create_or_update_daily_timesheet,
    get_daily_timesheet,
    get_daily_timesheets_by_filters,
    get_user_timesheets_for_date_range,
    delete_daily_timesheet,
    bulk_create_or_update_timesheets,
    get_team_timesheets_summary
)

router = APIRouter()

@router.post("", response_model=DailyTimesheetResponse, summary="Create or update daily timesheet")
async def create_or_update_timesheet(
    timesheet: DailyTimesheetCreate,
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    """
    Create or update a daily timesheet entry.
    
    This endpoint uses upsert logic - if an entry exists for the same
    org_id, project_id, user_id, and entry_date, it will be updated.
    Otherwise, a new entry will be created.
    """
    try:
        result = await create_or_update_daily_timesheet(timesheet, user.get("sub"))
        
        if result.data:
            return DailyTimesheetResponse(
                success=True,
                message="Daily timesheet saved successfully",
                data=result.data[0] if isinstance(result.data, list) else result.data
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to save timesheet")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save daily timesheet: {str(e)}")

@router.get("/{org_id}/{project_id}/{user_id}/{entry_date}", 
           response_model=DailyTimesheetResponse,
           summary="Get specific daily timesheet")
async def get_timesheet_by_details(
    org_id: str = Path(..., description="Organization ID"),
    project_id: str = Path(..., description="Project ID"),
    user_id: str = Path(..., description="User ID"),
    entry_date: date = Path(..., description="Entry date (YYYY-MM-DD)"),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    """Get a specific daily timesheet entry by org, project, user, and date."""
    try:
        result = await get_daily_timesheet(org_id, project_id, user_id, entry_date)
        
        if result.data:
            return DailyTimesheetResponse(
                success=True,
                message="Daily timesheet retrieved successfully",
                data=result.data
            )
        else:
            # Return empty timesheet structure for the requested date
            return DailyTimesheetResponse(
                success=True,
                message="No timesheet found for this date",
                data={
                    "org_id": org_id,
                    "project_id": project_id,
                    "user_id": user_id,
                    "entry_date": entry_date,
                    "in_progress": None,
                    "completed": None,
                    "blocked": None
                }
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch daily timesheet: {str(e)}")

@router.post("/search", response_model=DailyTimesheetListResponse, summary="Search daily timesheets")
async def search_timesheets(
    filters: DailyTimesheetFilters,
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    """
    Search daily timesheets based on provided filters.
    
    Returns timesheets with user and project details for better display.
    """
    try:
        result = await get_daily_timesheets_by_filters(filters)
        
        return DailyTimesheetListResponse(
            success=True,
            message="Daily timesheets retrieved successfully",
            data=result.data or [],
            total=len(result.data) if result.data else 0
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search daily timesheets: {str(e)}")

@router.get("/user/{user_id}/range", 
           response_model=DailyTimesheetListResponse,
           summary="Get user timesheets for date range")
async def get_user_timesheet_range(
    user_id: str = Path(..., description="User ID"),
    org_id: str = Query(..., description="Organization ID"),
    date_from: date = Query(..., description="Start date (YYYY-MM-DD)"),
    date_to: date = Query(..., description="End date (YYYY-MM-DD)"),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    """Get all timesheets for a specific user within a date range."""
    try:
        result = await get_user_timesheets_for_date_range(org_id, user_id, date_from, date_to)
        
        return DailyTimesheetListResponse(
            success=True,
            message="User timesheets retrieved successfully",
            data=result.data or [],
            total=len(result.data) if result.data else 0
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user timesheets: {str(e)}")

@router.delete("/{org_id}/{project_id}/{user_id}/{entry_date}",
              summary="Delete daily timesheet")
async def delete_timesheet(
    org_id: str = Path(..., description="Organization ID"),
    project_id: str = Path(..., description="Project ID"),
    user_id: str = Path(..., description="User ID"),
    entry_date: date = Path(..., description="Entry date (YYYY-MM-DD)"),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    """Delete a specific daily timesheet entry."""
    try:
        result = await delete_daily_timesheet(org_id, project_id, user_id, entry_date)
        
        return {
            "success": True,
            "message": "Daily timesheet deleted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete daily timesheet: {str(e)}")

@router.post("/bulk", response_model=DailyTimesheetListResponse, summary="Bulk create/update timesheets")
async def bulk_update_timesheets(
    bulk_data: DailyTimesheetBulkUpdate,
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    """
    Bulk create or update multiple timesheet entries.
    
    Useful for batch operations or importing timesheet data.
    """
    try:
        result = await bulk_create_or_update_timesheets(bulk_data.entries, user.get("sub"))
        
        return DailyTimesheetListResponse(
            success=True,
            message=f"Successfully processed {len(bulk_data.entries)} timesheet entries",
            data=result.data or [],
            total=len(result.data) if result.data else 0
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk update timesheets: {str(e)}")

@router.get("/team-summary/{org_id}/{entry_date}",
           summary="Get team timesheets summary")
async def get_team_summary(
    org_id: str = Path(..., description="Organization ID"),
    entry_date: date = Path(..., description="Entry date (YYYY-MM-DD)"),
    project_ids: Optional[List[str]] = Query(None, description="Filter by project IDs"),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    """
    Get a summary of team timesheets for a specific date.
    
    This endpoint is optimized for the timesheets UI, returning data
    in the format expected by the frontend components.
    """
    try:
        result = await get_team_timesheets_summary(org_id, entry_date, project_ids)
        
        return {
            "success": True,
            "message": "Team timesheets summary retrieved successfully",
            **result.data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch team summary: {str(e)}")

@router.put("/{org_id}/{project_id}/{user_id}/{entry_date}",
           response_model=DailyTimesheetResponse,
           summary="Update specific timesheet fields")
async def update_timesheet_fields(
    org_id: str = Path(..., description="Organization ID"),
    project_id: str = Path(..., description="Project ID"),
    user_id: str = Path(..., description="User ID"),
    entry_date: date = Path(..., description="Entry date (YYYY-MM-DD)"),
    updates: DailyTimesheetUpdate = ...,
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    """
    Update specific fields of an existing timesheet entry.
    
    This endpoint allows partial updates without overwriting the entire entry.
    """
    try:
        # Create a full timesheet object for the upsert operation
        timesheet_create = DailyTimesheetCreate(
            org_id=org_id,
            project_id=project_id,
            user_id=user_id,
            entry_date=entry_date,
            in_progress=updates.in_progress,
            completed=updates.completed,
            blocked=updates.blocked
        )
        
        result = await create_or_update_daily_timesheet(timesheet_create, user.get("sub"))
        
        if result.data:
            return DailyTimesheetResponse(
                success=True,
                message="Daily timesheet updated successfully",
                data=result.data[0] if isinstance(result.data, list) else result.data
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to update timesheet")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update daily timesheet: {str(e)}")
