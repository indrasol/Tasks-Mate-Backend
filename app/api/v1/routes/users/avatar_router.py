from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from typing import Optional
from io import BytesIO

from app.models.schemas.user_schema import UserAvatarResponse
from app.services.auth_handler import get_current_user
from app.services.avatar_service import upload_avatar
from app.services.organization_service import get_organizations_for_user
from app.core.db.supabase_db import get_supabase_client

router = APIRouter()


@router.post("/upload", response_model=UserAvatarResponse)
async def upload_user_avatar(
    file: UploadFile = File(...),
    org_name: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a user's avatar to Supabase storage.
    The avatar will be stored in 'avatars/{org_name}/{username}/{file_name}'
    """
    # Validate image file
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    try:
        # Read file content
        contents = await file.read()
        file_size = len(contents)
        
        # Check file size (limit to 5MB)
        if file_size > 5 * 1024 * 1024:  # 5MB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 5MB"
            )
        
        # Reset file pointer
        await file.seek(0)
        
        # Get username from user metadata or fallback to user ID
        username = current_user.get("username") or current_user.get("user_metadata", {}).get("username") or current_user.get("id", "unknown")
        
        # Get organization name - if not provided, try to get user's first organization
        org_folder = org_name
        if not org_folder:
            try:
                user_orgs = await get_organizations_for_user(
                    current_user.get("id"), 
                    username, 
                    current_user.get("email")
                )
                if user_orgs and len(user_orgs) > 0:
                    org_folder = user_orgs[0].get("name", "default")
                else:
                    org_folder = "default"
            except Exception:
                org_folder = "default"
        
        # Upload file to Supabase
        avatar_url = await upload_avatar(
            file_content=contents,
            filename=file.filename,
            user_id=current_user.get("id"),
            username=username,
            org_name=org_folder
        )
        
        return {"avatar_url": avatar_url}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading avatar: {str(e)}"
        )
