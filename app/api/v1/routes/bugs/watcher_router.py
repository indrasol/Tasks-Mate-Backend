from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.services.auth_handler import verify_token
from app.services.bug_service import add_bug_watcher, remove_bug_watcher, list_bug_watchers

router = APIRouter(prefix="/watchers", tags=["bug_watchers"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def add_watcher_to_bug(
    bug_id: str,
    current_user: dict = Depends(verify_token)
):
    """Add the current user as a watcher to a bug."""
    try:
        result = await add_bug_watcher(bug_id, current_user["username"])
        if not result or not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add watcher"
            )
        return result.data[0] if isinstance(result.data, list) else result.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_watcher_from_bug(
    bug_id: str,
    username: str,
    current_user: dict = Depends(verify_token)
):
    """Remove a watcher from a bug."""
    try:
        # Only allow users to remove themselves unless they're an admin
        if username != current_user["username"]:
            # TODO: Add admin check here
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only remove yourself as a watcher"
            )
            
        result = await remove_bug_watcher(bug_id, username)
        if not result or not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Watcher not found"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("", response_model=List[dict])
async def list_bug_watchers(
    bug_id: str,
    current_user: dict = Depends(verify_token)
):
    """List all watchers for a bug."""
    try:
        result = await list_bug_watchers(bug_id)
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    

