from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.services.auth_handler import verify_token
from app.services.bug_service import create_bug_comment, get_bug_comments, update_bug_comment, delete_bug_comment
from app.models.schemas.bug import BugCommentCreate, BugCommentUpdate, BugCommentInDB
from app.api.v1.routes.emails.email_routes import send_bug_comment_email

router = APIRouter(prefix="/comments", tags=["bug_comments"])

@router.post("", response_model=BugCommentInDB, status_code=status.HTTP_201_CREATED)
async def add_comment_to_bug(
    bug_id: str,
    comment: BugCommentCreate,
    current_user: dict = Depends(verify_token)
):
    """Add a comment to a bug."""
    try:
        result = await create_bug_comment(bug_id, comment, current_user["username"])
        if not result or not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add comment"
            )
        
        # Send comment email if there are mentions
        created_comment = result.data[0] if isinstance(result.data, list) else result.data
        if created_comment.get("mentions"):
            await send_bug_comment_email(created_comment)
        
        return created_comment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("", response_model=List[BugCommentInDB])
async def list_bug_comments(
    bug_id: str,
    current_user: dict = Depends(verify_token)
):
    """List all comments for a bug."""
    try:
        comments = await get_bug_comments(bug_id)
        return comments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{comment_id}", response_model=BugCommentInDB)
async def update_comment(
    bug_id: str,
    comment_id: str,
    comment_update: BugCommentUpdate,
    current_user: dict = Depends(verify_token)
):
    """Update a bug comment."""
    try:

        existing = await get_bug_comment(comment_id)
        if not existing or not existing.data:
            raise HTTPException(status_code=404, detail="Not found")

        existing_mentions = existing.data.get("mentions")

        result = await update_bug_comment(
            bug_id=bug_id,
            comment_id=comment_id,
            comment_data=comment_update,
            username=current_user["username"]
        )
        if not result or not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found or update failed"
            )
        # return result.data[0] if isinstance(result.data, list) else result.data
        # Send comment email if there are mentions
        created_comment = result.data[0] if isinstance(result.data, list) else result.data
        if created_comment.get("mentions"):
            # Check for changes in mentions compared to existing by comparing each element
            mentions_changed = any(x not in existing_mentions for x in created_comment["mentions"]) or any(x not in created_comment["mentions"] for x in existing_mentions)
            if mentions_changed:
                await send_bug_comment_email(created_comment.model_dump())
        
        return created_comment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    bug_id: str,
    comment_id: str,
    current_user: dict = Depends(verify_token)
):
    """Delete a bug comment."""
    try:
        result = await delete_bug_comment(
            bug_id=bug_id,
            comment_id=comment_id,
            username=current_user["username"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
