from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse
import logging

from app.services.auth_handler import verify_token
from app.api.v1.routes.organizations.org_rbac import org_rbac
from app.models.schemas.user_timesheet import (
    UserTimesheetCreate,
    UserTimesheetResponse,
    TeamTimesheetsResponse,
    CalendarStatusResponse
)
from app.services.user_timesheet_service import (
    create_or_update_user_timesheet_field,
    get_user_timesheet_for_date,
    get_team_timesheets_for_date,
    get_calendar_month_status,
    delete_user_timesheet
)

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/field", response_model=UserTimesheetResponse, summary="Update timesheet field")
async def update_timesheet_field(
    timesheet: UserTimesheetCreate,
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    """
    Update a specific field in user's timesheet.
    
    This endpoint handles creating or updating individual timesheet fields
    (in_progress, completed, blocked) for a specific user and date.
    
    **Permission Requirements:**
    - Users can update their own timesheets
    - Org admins/owners can update any user's timesheet
    """
    try:
        # Validate permissions - users can only edit their own timesheets unless they're admin/owner
        current_user_id = user.get("id")  # Fixed: use "id" instead of "sub"
        user_org_role = org_role if org_role else None
        
        if timesheet.user_id != current_user_id and user_org_role not in ['owner', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own timesheets"
            )
        
        # Validate field content length
        if len(timesheet.field_content) > 5000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Field content too long (max 5000 characters)"
            )
        
        result = await create_or_update_user_timesheet_field(
            timesheet.org_id,
            timesheet.user_id,
            timesheet.entry_date,
            timesheet.field_type,
            timesheet.field_content
        )
        
        if result and result.data:
            logger.info(f"User {current_user_id} updated {timesheet.field_type} for user {timesheet.user_id} on {timesheet.entry_date}")
            return UserTimesheetResponse(
                success=True,
                message="Timesheet field updated successfully",
                data=result.data[0] if isinstance(result.data, list) else result.data
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update timesheet field"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating timesheet field: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update timesheet: {str(e)}"
        )

@router.get("/user/{user_id}/{entry_date}", response_model=UserTimesheetResponse, summary="Get user timesheet")
async def get_user_timesheet(
    user_id: str = Path(..., description="User ID"),
    entry_date: date = Path(..., description="Entry date (YYYY-MM-DD)"),
    org_id: str = Query(..., description="Organization ID"),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    """
    Get user's timesheet for a specific date.
    
    Returns the complete timesheet data structure for a user on a given date,
    or an empty structure if no timesheet exists.
    
    **Permission Requirements:**
    - Users can view their own timesheets
    - Org members can view other members' timesheets (for collaboration)
    - Org admins/owners can view all timesheets
    """
    try:
        # Validate permissions
        current_user_id = user.get("id")  # Fixed: use "id" instead of "sub"
        user_org_role = org_role if org_role else None
        
        # Allow viewing if user is viewing their own timesheet or is org member/admin/owner
        if user_id != current_user_id and user_org_role not in ['member', 'admin', 'owner']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this timesheet"
            )
        
        result = await get_user_timesheet_for_date(org_id, user_id, entry_date)
        
        logger.info(f"User {current_user_id} fetched timesheet for user {user_id} on {entry_date}")
        return UserTimesheetResponse(
            success=True,
            message="User timesheet retrieved successfully",
            data=result["data"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user timesheet: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch timesheet: {str(e)}"
        )

@router.get("/team/{org_id}/{entry_date}", summary="Get team timesheets")
async def get_team_timesheets(
    org_id: str = Path(..., description="Organization ID"),
    entry_date: date = Path(..., description="Entry date (YYYY-MM-DD)"),
    user_ids: Optional[List[str]] = Query(None, description="Filter by specific user IDs"),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    """
    Get team timesheets for a specific date.
    
    Returns timesheets for all organization members (or filtered subset)
    for the specified date. This is the main endpoint used by the calendar view.
    
    **Permission Requirements:**
    - Org members can view team timesheets (for collaboration and transparency)
    - Org admins/owners can view all timesheets
    """
    try:
        # Validate permissions - must be org member or higher
        user_org_role = org_role if org_role else None
        if user_org_role not in ['member', 'admin', 'owner']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be an organization member to view team timesheets"
            )
        
        result = await get_team_timesheets_for_date(org_id, entry_date, user_ids)
        
        current_user_id = user.get("id")  # Fixed: use "id" instead of "sub"
        logger.info(f"User {current_user_id} fetched team timesheets for {org_id} on {entry_date}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Team timesheets retrieved successfully",
                **result["data"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching team timesheets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch team timesheets: {str(e)}"
        )

@router.get("/calendar-status/{org_id}/{year}/{month}", summary="Get calendar month status")
async def get_calendar_status(
    org_id: str = Path(..., description="Organization ID"),
    year: int = Path(..., description="Year", ge=2020, le=2030),
    month: int = Path(..., description="Month", ge=1, le=12),
    user_ids: Optional[List[str]] = Query(None, description="Filter by specific user IDs"),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    """
    Get calendar month status for timesheet indicators.
    
    Returns a lightweight summary of which dates have timesheet data
    for the specified month. Used to display calendar indicators.
    
    **Permission Requirements:**
    - Org members can view calendar status (for planning and coordination)
    - Org admins/owners can view all calendar data
    """
    try:
        # Validate permissions - must be org member or higher
        user_org_role = org_role if org_role else None
        current_user_id = user.get("id")  # Fixed: use "id" instead of "sub"
        
        if user_org_role not in ['member', 'admin', 'owner']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be an organization member to view calendar status"
            )
        
        result = await get_calendar_month_status(org_id, year, month, user_ids)
        
        logger.info(f"User {current_user_id} fetched calendar status for {org_id} {year}-{month:02d}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Calendar status retrieved successfully",
                **result
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching calendar status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch calendar status: {str(e)}"
        )

@router.delete("/user/{user_id}/{entry_date}", summary="Delete user timesheet")
async def delete_user_timesheet_endpoint(
    user_id: str = Path(..., description="User ID"),
    entry_date: date = Path(..., description="Entry date (YYYY-MM-DD)"),
    org_id: str = Query(..., description="Organization ID"),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    """
    Delete a user's timesheet for a specific date.
    
    Completely removes the timesheet entry for the specified user and date.
    This action cannot be undone.
    
    **Permission Requirements:**
    - Users can delete their own timesheets
    - Org admins/owners can delete any user's timesheet
    """
    try:
        # Validate permissions - users can only delete their own timesheets unless they're admin/owner
        current_user_id = user.get("id")  # Fixed: use "id" instead of "sub"
        user_org_role = org_role if org_role else None
        
        if user_id != current_user_id and user_org_role not in ['owner', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own timesheets"
            )
        
        result = await delete_user_timesheet(org_id, user_id, entry_date)
        
        logger.info(f"User {current_user_id} deleted timesheet for user {user_id} on {entry_date}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Timesheet deleted successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting timesheet: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete timesheet: {str(e)}"
        )

@router.get("/health", summary="Health check")
async def health_check():
    """Simple health check endpoint for the user timesheet service."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "User timesheet service is healthy",
            "service": "user_timesheet_router",
            "version": "1.0.0"
        }
    )
