from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional
from app.services.auth_handler import verify_token
from app.services.bug_attachment_service import upload_and_create_bug_attachment, list_bug_attachments, delete_bug_attachment, update_bug_attachment
from app.models.schemas.bug_attachment import BugAttachmentInDB, BugAttachmentUpdate

router = APIRouter(prefix="/attachments", tags=["bug_attachments"])

@router.post("", response_model=BugAttachmentInDB, status_code=status.HTTP_201_CREATED)
async def upload_bug_attachment(
    bug_id: str,
    title: Optional[str] = Form(None),
    is_inline: Optional[bool] = Form(None),
    file: UploadFile = File(...),
    current_user: dict = Depends(verify_token)
):
    """Upload an attachment for a bug."""
    try:
        # result = await create_bug_attachment(bug_id, file, current_user["username"])
        # if not result or not result.data:
        #     raise HTTPException(
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         detail="Failed to upload attachment"
        #     )
        # return result.data[0] if isinstance(result.data, list) else result.data
        data = await upload_and_create_bug_attachment(
            bug_id=bug_id,
            file=file,
            title=title,
            user_id=current_user["id"],
            username=current_user.get("username") or current_user.get("email") or current_user["id"],
            bug_title="",
            is_inline=is_inline
        )
        return data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("", response_model=List[BugAttachmentInDB])
async def list_attachments(
    bug_id: str,
    current_user: dict = Depends(verify_token)
):
    """List all attachments for a bug."""
    try:
        # return await list_bug_attachments(bug_id)
        result = await list_bug_attachments(bug_id)
        # Extract data from Supabase response
        attachments = result.data if hasattr(result, 'data') else []
        return attachments
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
        result = await delete_bug_attachment(attachment_id, current_user["username"])
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


@router.put("/{attachment_id}", response_model=BugAttachmentInDB)
async def update_attachment(
    attachment_id: str,
    attachment: BugAttachmentUpdate,
    bug_id: str,
    user=Depends(verify_token)
):
    try:
        result = await update_bug_attachment(
            attachment_id,
            attachment.dict(exclude_unset=True),
            user_id=user["username"],
            bug_title="",
        )
        return result.get("data", [result])[0] if hasattr(result, "get") else result
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update attachment")


