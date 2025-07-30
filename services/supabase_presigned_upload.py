from core.db.supabase_db import get_supabase_client
from config import settings
from uuid import uuid4
from datetime import timedelta


def generate_supabase_presigned_upload(file_name: str):
    file_key = f"{uuid4()}_{file_name}"

    supabase = get_supabase_client()

    # Upload placeholder empty file so that we can sign URL
    supabase.storage.from_(settings.SUPABASE_BUCKET_NAME).upload(file_key, b"", {"contentType": "application/octet-stream", "upsert": True})

    # Generate signed upload URL (valid for 60 mins)
    signed_url_data = supabase.storage.from_(settings.SUPABASE_BUCKET_NAME).create_signed_url(file_key, expires_in=60 * 60)

    return {
        "upload_url": signed_url_data["signedURL"],
        "file_url": f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_BUCKET_NAME}/{file_key}",
        "file_name": file_name
    }
