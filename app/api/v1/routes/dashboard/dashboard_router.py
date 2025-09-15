from fastapi import APIRouter, Depends, HTTPException
from app.services.auth_handler import verify_token
from app.services.dashboard_service import get_dashboard_data, get_user_dashboard_data
from app.models.schemas.dashboard import DashboardResponse, DashboardData, UserDashboardResponse, UserDashboardData
from app.api.v1.routes.organizations.org_rbac import org_rbac

router = APIRouter()

@router.get("/{org_id}", response_model=DashboardResponse)
async def get_organization_dashboard(org_id: str, user=Depends(verify_token), org_role=Depends(org_rbac)):
    """
    Get dashboard data for a specific organization.
    
    Args:
        org_id: The ID of the organization
        user: The authenticated user (provided by dependency)
        org_role: The user's role in the organization (provided by dependency)
        
    Returns:
        Dashboard data for the organization
        
    Raises:
        HTTPException: If the user is not authorized or if there's an error fetching data
    """
    # Verify that the user has access to the organization
    if not org_role:
        raise HTTPException(status_code=403, detail="Not authorized to access this organization's dashboard")
    
    try:
        # Get dashboard data from the service
        dashboard_data = await get_dashboard_data(org_id)
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard data: {str(e)}")


@router.get("/user/{user_id}", response_model=UserDashboardResponse)
async def get_user_dashboard(user_id: str, user=Depends(verify_token)):
    """
    Get dashboard data for a specific user.
    
    Args:
        user_id: The ID of the user
        user: The authenticated user (provided by dependency)
        
    Returns:
        Dashboard data for the user
        
    Raises:
        HTTPException: If the user is not authorized or if there's an error fetching data
    """
    # Verify that the user can access their own dashboard or is an admin
    if user.get("id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this user's dashboard")
    
    try:
        # Get user dashboard data from the service
        user_dashboard_data = await get_user_dashboard_data(user_id)
        return user_dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user dashboard data: {str(e)}")
