import os
import uuid
from datetime import datetime
from typing import Optional

from app.core.db.supabase_db import get_supabase_client
from app.services.auth_handler import get_current_user_id


async def upload_avatar(
    file_content: bytes,
    filename: str,
    user_id: str,
    username: str,
    org_name: str = "default"
) -> str:
    """
    Upload user avatar to Supabase storage.
    
    Args:
        file_content: File content as bytes
        filename: Original filename
        user_id: User ID for metadata and unique storage path
        username: Username for display purposes (not used in storage path)
        org_name: Organization name (deprecated, not used in storage path)
        
    Returns:
        URL to the uploaded avatar
    """
    # Get file extension
    _, file_extension = os.path.splitext(filename)
    
    # Create a unique filename to avoid collisions
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Construct path using user_id to ensure uniqueness: avatars/{user_id}/{unique_filename}
    # This ensures each user has their own isolated avatar storage regardless of organization/username
    storage_path = f"avatars/{user_id}/{unique_filename}"
    
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Upload file bytes to Supabase storage
    response = supabase.storage.from_("avatars").upload(
        path=storage_path,
        file=file_content,
        file_options={"content-type": "image/*"}
    )

    if getattr(response, "error", None):
        raise Exception(f"Supabase storage error: {response.error}")
    
    # Get public URL
    public_resp = supabase.storage.from_("avatars").get_public_url(storage_path)
    if isinstance(public_resp, dict):
        avatar_url = public_resp.get("publicUrl")
    else:
        avatar_url = str(public_resp)

    if not avatar_url:
        raise Exception("Failed to retrieve public avatar URL")
    
    # Update user metadata with avatar URL
    update_response = supabase.auth.admin.update_user_by_id(
        user_id,
        {
            "user_metadata": {
                "avatar_url": avatar_url,
                "avatar_updated_at": datetime.now().isoformat()
            }
        }
    )

    if getattr(update_response, "error", None):
        raise Exception(f"Failed to update user metadata: {update_response.error}")
    
    return avatar_url


async def get_avatar_url(user_id: str) -> Optional[str]:
    """
    Get the avatar URL from the user's metadata.
    
    Args:
        user_id: User ID
        
    Returns:
        Avatar URL or None if not found
    """
    supabase = get_supabase_client()
    
    user = supabase.auth.admin.get_user_by_id(user_id)
    
    if user.get("error"):
        return None
    
    return user.get("data", {}).get("user_metadata", {}).get("avatar_url")
