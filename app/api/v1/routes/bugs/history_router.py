from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.services.auth_handler import verify_token
from app.services.bug_service import get_bug_activity_logs, get_activity_detail
from app.models.schemas.bug import BugActivityLogInDB

router = APIRouter(prefix="/history", tags=["bug_history"])

@router.get("", response_model=List[BugActivityLogInDB])
async def get_bug_history(
    bug_id: str,
    limit: int = Query(50, ge=1, description="Number of history items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: dict = Depends(verify_token)
):
    """Get activity history for a bug."""
    try:
        result = await get_bug_activity_logs(
            bug_id=bug_id,
            limit=limit,
            offset=offset
        )
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{activity_id}", response_model=BugActivityLogInDB)
async def get_activity_detail(
    bug_id: str,
    activity_id: str,
    current_user: dict = Depends(verify_token)
):
    """Get details of a specific activity log entry."""
    try:
        result = await get_activity_detail(
            bug_id=bug_id,
            activity_id=activity_id
        )
        return result.data if result.data else None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
