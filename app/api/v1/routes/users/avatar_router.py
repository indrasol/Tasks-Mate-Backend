from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from typing import Optional
from io import BytesIO

from app.models.schemas.user_schema import UserAvatarResponse
from app.services.auth_handler import get_current_user
from app.services.avatar_service import upload_avatar

router = APIRouter()


@router.post("/upload", response_model=UserAvatarResponse)
async def upload_user_avatar(
    file: UploadFile = File(...),
    org_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a user's avatar to Supabase storage.
    The avatar will be stored in '{bucket}/{org_id}/{user_id}/{unique_filename}' to ensure proper organization.
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
        
        # Get username for display purposes (still needed for user metadata)
        username = current_user.get("username") or current_user.get("user_metadata", {}).get("username") or current_user.get("id", "unknown")
        
        # Use provided org_id or default
        org_id_to_use = org_id or "default"
        
        # Upload file to Supabase with proper folder structure
        avatar_url = await upload_avatar(
            file_content=contents,
            filename=file.filename,
            user_id=current_user.get("id"),
            username=username,
            org_id=org_id_to_use
        )
        
        return {"avatar_url": avatar_url}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading avatar: {str(e)}"
        )
