from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from app.services.auth_handler import verify_token
from app.services.bug_service import get_bug_dependencies

router = APIRouter(prefix="/dependencies", tags=["bug_dependencies"])

@router.get("", response_model=List[Dict[str, Any]])
async def list_bug_dependencies(
    bug_id: str,
    current_user: dict = Depends(verify_token)
):
    """List all dependencies for a bug."""
    try:
        dependencies = await get_bug_dependencies(bug_id)
        return dependencies
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
