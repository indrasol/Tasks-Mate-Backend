from fastapi import APIRouter, Depends, Query
from services.auth_handler import get_current_user
from services.supabase_presigned_upload import generate_supabase_presigned_upload

router = APIRouter(prefix="/api", tags=["Task Attachments"])


@router.get("/attachments/supabase-presign")
async def get_supabase_signed_upload_url(
    file_name: str = Query(...),
    user: dict = Depends(get_current_user)
):
    return generate_supabase_presigned_upload(file_name)
