from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List
from app.services.auth_handler import verify_token
from app.services.bug_service import create_bug_attachment, list_bug_attachments, delete_bug_attachment
from app.models.schemas.bug import BugAttachmentInDB

router = APIRouter(prefix="/attachments", tags=["bug_attachments"])

@router.post("", response_model=BugAttachmentInDB, status_code=status.HTTP_201_CREATED)
async def upload_bug_attachment(
    bug_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(verify_token)
):
    """Upload an attachment for a bug."""
    try:
        result = await create_bug_attachment(bug_id, file, current_user["username"])
        if not result or not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload attachment"
            )
        return result.data[0] if isinstance(result.data, list) else result.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("", response_model=List[BugAttachmentInDB])
async def list_bug_attachments(
    bug_id: str,
    current_user: dict = Depends(verify_token)
):
    """List all attachments for a bug."""
    try:
        result = await list_bug_attachments(bug_id)
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    bug_id: str,
    attachment_id: str,
    current_user: dict = Depends(verify_token)
):
    """Delete a bug attachment."""
    try:
        result = await delete_bug_attachment(bug_id, attachment_id, current_user["username"])
        if not result or not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
