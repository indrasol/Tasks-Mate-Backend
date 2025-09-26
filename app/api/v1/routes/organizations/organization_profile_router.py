from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.responses import JSONResponse
import logging

from app.services.auth_handler import verify_token
from app.api.v1.routes.organizations.org_rbac import org_rbac
from app.models.schemas.organization_profile import (
    OrganizationProfileCreate,
    OrganizationProfileUpdate,
    OrganizationProfileResponse
)
from app.services.organization_profile_service import (
    get_organization_profile,
    create_or_update_organization_profile,
    delete_organization_profile
)

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{org_id}", summary="Get organization profile")
async def get_org_profile(
    org_id: str = Path(..., description="Organization ID"),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    """
    Get organization profile.
    
    Returns the complete organization profile including mission, vision, 
    core values, and other organizational information.
    
    **Permission Requirements:**
    - All organization members can view the profile
    """
    try:
        # Validate permissions - must be org member or higher
        current_user_id = user.get("id")
        user_org_role = org_role if org_role else None
        
        if user_org_role not in ['member', 'admin', 'owner']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be an organization member to view the profile"
            )
        
        result = await get_organization_profile(org_id)
        
        logger.info(f"User {current_user_id} fetched organization profile for org {org_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Organization profile retrieved successfully",
                "data": result["data"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching organization profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch organization profile: {str(e)}"
        )

@router.put("/{org_id}", summary="Update organization profile")
async def update_org_profile(
    profile_data: OrganizationProfileUpdate,
    org_id: str = Path(..., description="Organization ID"),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    """
    Update organization profile.
    
    Updates the organization's mission, vision, core values, and other 
    organizational information. Only owners and admins can make changes.
    
    **Permission Requirements:**
    - Organization owners and admins can edit the profile
    """
    try:
        # Validate permissions - only owners and admins can edit
        current_user_id = user.get("id")
        user_org_role = org_role if org_role else None
        
        if user_org_role not in ['admin', 'owner']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organization owners and admins can edit the profile"
            )
        
        result = await create_or_update_organization_profile(org_id, profile_data, current_user_id)
        
        logger.info(f"User {current_user_id} updated organization profile for org {org_id}")
        
        # Return the updated data
        updated_profile = await get_organization_profile(org_id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Organization profile updated successfully",
                "data": updated_profile["data"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating organization profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update organization profile: {str(e)}"
        )

@router.post("/{org_id}", summary="Create organization profile")
async def create_org_profile(
    profile_data: OrganizationProfileCreate,
    org_id: str = Path(..., description="Organization ID"),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    """
    Create organization profile.
    
    Creates a new organization profile with mission, vision, core values, 
    and other organizational information.
    
    **Permission Requirements:**
    - Organization owners and admins can create the profile
    """
    try:
        # Validate permissions - only owners and admins can create
        current_user_id = user.get("id")
        user_org_role = org_role if org_role else None
        
        if user_org_role not in ['admin', 'owner']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organization owners and admins can create the profile"
            )
        
        result = await create_or_update_organization_profile(org_id, profile_data, current_user_id)
        
        logger.info(f"User {current_user_id} created organization profile for org {org_id}")
        
        # Return the created data
        created_profile = await get_organization_profile(org_id)
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "message": "Organization profile created successfully",
                "data": created_profile["data"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating organization profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create organization profile: {str(e)}"
        )

@router.delete("/{org_id}", summary="Delete organization profile")
async def delete_org_profile(
    org_id: str = Path(..., description="Organization ID"),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    """
    Delete organization profile.
    
    Completely removes the organization profile. This action cannot be undone.
    
    **Permission Requirements:**
    - Only organization owners can delete the profile
    """
    try:
        # Validate permissions - only owners can delete
        current_user_id = user.get("id")
        user_org_role = org_role if org_role else None
        
        if user_org_role != 'owner':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organization owners can delete the profile"
            )
        
        result = await delete_organization_profile(org_id, current_user_id)
        
        logger.info(f"User {current_user_id} deleted organization profile for org {org_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Organization profile deleted successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting organization profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete organization profile: {str(e)}"
        )

@router.get("/health", summary="Health check")
async def health_check():
    """Simple health check endpoint for the organization profile service."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Organization profile service is healthy",
            "service": "organization_profile_router",
            "version": "1.0.0"
        }
    )
