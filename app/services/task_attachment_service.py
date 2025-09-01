# app/services/task_attachment_service.py
import os
import datetime
import re
import mimetypes
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, UploadFile

from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from app.services.task_history_service import record_history

# Config
ATTACHMENTS_BUCKET = os.getenv("ATTACHMENTS_BUCKET", "task-attachments")  # keep your existing name
ATTACHMENTS_LIMIT = int(os.getenv("ATTACHMENTS_LIMIT", "5"))

ATTACHMENT_UPDATE_WHITELIST = ["title", "is_inline", "filename", "url", "path"]

# ────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────

async def _generate_sequential_attachment_id() -> str:
    """Generate a random attachment ID with prefix 'A' and 4 digits, ensuring uniqueness."""
    sb = get_supabase_client()
    digits = 4
    for _ in range(10):
        candidate = f"A{__import__('random').randint(0, 10**digits - 1):0{digits}d}"
        def op():
            return sb.from_("task_attachments").select("attachment_id").eq("attachment_id", candidate).limit(1).execute()
        res = await safe_supabase_operation(op, "Failed to verify attachment id uniqueness")
        if not res or not getattr(res, "data", None):
            return candidate
    ts = int(datetime.datetime.utcnow().timestamp()) % (10**digits)
    return f"A{ts:0{digits}d}"

def _diff_attachment(old: Dict[str, Any], new: Dict[str, Any]) -> List[Dict[str, Any]]:
    changes = []
    for f in ATTACHMENT_UPDATE_WHITELIST:
        if old.get(f) != new.get(f):
            changes.append({"field": f, "old": old.get(f), "new": new.get(f)})
    return changes

async def _enforce_task_limit(task_id: str):
    """Raise 400 if non-deleted attachments >= ATTACHMENTS_LIMIT."""
    sb = get_supabase_client()
    def op():
        return (
            sb.from_("task_attachments")
            .select("attachment_id", count="exact")
            .eq("task_id", task_id)
            .is_("deleted_at", None)
            .is_("is_inline", None)
            .execute()
        )
    res = await safe_supabase_operation(op, "Failed to count attachments")
    count_val = getattr(res, "count", None) or (res.data and len(res.data)) or 0
    if count_val >= ATTACHMENTS_LIMIT:
        raise HTTPException(
            status_code=400,
            detail=f"Attachment limit reached ({ATTACHMENTS_LIMIT} per task)."
        )

def _extract_public_url(url_result: Any) -> str:
    """
    supabase-py v2 returns dict-like { 'data': {'publicUrl': '...'} }
    Be defensive across minor version diffs.
    """
    if isinstance(url_result, dict):
        data = url_result.get("data") or {}
        return data.get("publicUrl") or data.get("public_url") or ""
    # some clients return str directly
    if isinstance(url_result, str):
        return url_result
    # last resort
    maybe = getattr(url_result, "public_url", None) or getattr(url_result, "publicUrl", None)
    return str(maybe or "")

def _guess_content_type(filename: str, fallback: str = "application/octet-stream") -> str:
    # Robust mapping for common types where mimetypes may be incomplete
    lower = filename.lower()
    ext_map = {
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
        ".pdf": "application/pdf",
    }
    for ext, ctype in ext_map.items():
        if lower.endswith(ext):
            return ctype
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or fallback

async def _next_attachment_id_retry(sb, tries=5):
    for _ in range(tries):
        aid = await _generate_sequential_attachment_id()
        try:
            # cheap existence check; or just try insert and catch conflict
            exists = sb.from_("task_attachments").select("attachment_id").eq("attachment_id", aid).limit(1).execute()
            if not exists.data:
                return aid
        except Exception:
            return aid
    # last resort, time-based suffix
    ts = int(datetime.datetime.utcnow().timestamp()) % 10000
    return f"A{ts:04d}"

def _safe_storage_path(prefix: str, original: str, existing: set[str]) -> str:
    """Ensure unique filename under given prefix path (e.g. org_id/task_id)."""
    base, dot, ext = original.rpartition(".")
    if not base:
        base, ext, dot = original, "", ""
    path = f"{prefix}/{original}"
    i = 1
    while path in existing:
        candidate = f"{base} ({i}){dot}{ext}" if ext else f"{base} ({i})"
        path = f"{prefix}/{candidate}"
        i += 1
    return path

async def _list_existing_paths(sb, task_id: str) -> set[str]:
    try:
        # Supabase list with prefix, returns dict with 'data' (list of objects with 'name')
        listing = sb.storage.from_(ATTACHMENTS_BUCKET).list(path=task_id, search="")
        names = [o.get("name") for o in (listing or []) if isinstance(o, dict)]
        return {f"{task_id}/{n}" for n in names if n}
    except Exception:
        return set()

def _sanitize_name(name: str) -> str:
    name = name.replace("\\", "/").split("/")[-1]  # drop any path
    # allow letters, numbers, space, dot, dash, underscore, parentheses
    return re.sub(r"[^A-Za-z0-9 ._\-()]", "_", name)[:255]

# ────────────────────────────────────────────────────────────
# Primary “upload + create” API
# ────────────────────────────────────────────────────────────

async def upload_and_create_task_attachment(
    *,
    task_id: str,
    file: UploadFile,
    title: Optional[str],
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    actor_display: Optional[str] = None,
    task_title: Optional[str] = None,
    is_inline: Optional[bool] = None
) -> Dict[str, Any]:
    """
    - Enforce per-task limit
    - Generate sequential id A0001...
    - Upload to storage: {task_id}/{original_filename}
    - Fetch public URL
    - Create DB row with the public URL
    - Log 'attachment_created'
    """
    await _enforce_task_limit(task_id)

    sb = get_supabase_client()
    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat()

    # 1) Generate ID & determine org prefix
    attachment_id = await _next_attachment_id_retry(sb)

    # Fetch org_id via project (tasks table has project_id)
    try:
        proj_res = (
            sb.from_("tasks")
            .select("org_id,project_id")
            .eq("task_id", task_id)
            .single()
            .execute()
        )
        org_id_val = proj_res.data.get("org_id") if proj_res and proj_res.data else "unknown"
    except Exception:
        org_id_val = "unknown"

    prefix_path = f"{org_id_val}/{task_id}"

    original_name = _sanitize_name(title or file.filename or "file")
    storage_path = f"{prefix_path}/{original_name}"

    # 2) Upload to storage
    # Note: use upsert=False to avoid overwriting; you can switch to True if desired
    try:
        # Ensure unique storage path under this task
        existing = await _list_existing_paths(sb, prefix_path)
        storage_path = _safe_storage_path(prefix_path, original_name, existing)

        # Read the uploaded file as bytes to satisfy clients that don't accept SpooledTemporaryFile
        file_bytes = await file.read()

        # Choose the best content type available
        content_type = _guess_content_type(original_name)
        if content_type in ("application/octet-stream", "text/plain"):
            # Try by extension when generic or plain text
            content_type = _guess_content_type(original_name, fallback="application/octet-stream")

        sb.storage.from_(ATTACHMENTS_BUCKET).upload(
            storage_path,
            file=file_bytes,
            file_options={
                # Use header-style keys per storage-py docs so content-type is honored
                "content-type": content_type,
                "x-upsert": "true",
                # One-year public cache
                "cache-control": "max-age=31536000, public",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {e}")

    # 3) Get public URL
    try:
        url_result = sb.storage.from_(ATTACHMENTS_BUCKET).get_public_url(storage_path)
        public_url = _extract_public_url(url_result)
        if not public_url:
            raise RuntimeError("Empty public URL from storage")
    except Exception as e:
        # attempt cleanup (best effort)
        try:
            sb.storage.from_(ATTACHMENTS_BUCKET).remove([storage_path])
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to get public URL: {e}")

    # 4) Insert DB row
    row = {
        "attachment_id": attachment_id,
        "task_id": task_id,
        "title": title or original_name,
        "name": original_name,
        # store both for backward compatibility
        "storage_path": storage_path,
        "name": original_name,
        "url": public_url,
        "uploaded_by": username,
        "uploaded_at": now,
        "is_inline":is_inline
    }

    def op_insert():
        return sb.from_("task_attachments").insert(row).execute()

    result = await safe_supabase_operation(op_insert, "Failed to create task attachment")
    data = result.data[0] if isinstance(result.data, list) else result.data

    if not is_inline:
        # 5) History
        await record_history(
            task_id=task_id,
            action="attachment_created",
            created_by=username or (user_id or ""),
            title=task_title,
            metadata={"attachment_id": attachment_id, "filename": original_name, "url": public_url},
            actor_display=None,
        )

    return data

# ────────────────────────────────────────────────────────────
# Existing CRUD: small alignment with record_history
# ────────────────────────────────────────────────────────────

async def create_task_attachment(data: dict, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Leave available for legacy path (when client already uploaded)."""
    await _enforce_task_limit(data["task_id"])

    # Ensure ID if not provided
    data.setdefault("attachment_id", await _generate_sequential_attachment_id())

    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
    data.setdefault("created_at", now)
    data.setdefault("uploaded_at", now)
    if user_id:
        data.setdefault("uploaded_by", user_id)

    sb = get_supabase_client()
    def op():
        return sb.from_("task_attachments").insert(data).execute()

    result = await safe_supabase_operation(op, "Failed to create task attachment")

    if user_id and result.data:
        created = result.data[0] if isinstance(result.data, list) else result.data
        await record_history(
            task_id=created["task_id"],
            action="attachment_created",
            created_by=user_id,
            title=None,
            metadata={
                "attachment_id": created.get("attachment_id"),
                "filename": created.get("filename") or created.get("name"),
                "url": created.get("url"),
            },
            actor_display=user_id,
        )
    return result


async def get_task_attachment(attachment_id: str):
    sb = get_supabase_client()
    def op():
        return sb.from_("task_attachments").select("*").eq("attachment_id", attachment_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch task attachment")


async def update_task_attachment(attachment_id: str, data: dict, user_id: Optional[str] = None, task_title: Optional[str] = None) -> Dict[str, Any]:
    current = await get_task_attachment(attachment_id)
    if not current or not current.data:
        raise HTTPException(status_code=404, detail="Attachment not found")
    before = current.data[0] if isinstance(current.data, list) else current.data

    after = {**before, **data}
    changes = _diff_attachment(before, after)

    sb = get_supabase_client()
    def op():
        return sb.from_("task_attachments").update(data).eq("attachment_id", attachment_id).execute()

    result = await safe_supabase_operation(op, "Failed to update task attachment")

    if user_id and changes:
        # Add a context object first so UI can display filename and link even if it wasn't changed
        context = {
            "attachment_id": before.get("attachment_id"),
            "filename": before.get("name") or before.get("filename"),
            "url": before.get("url"),
        }
        meta = [context] + changes
        await record_history(
            task_id=before["task_id"],
            action="attachment_updated",
            created_by=user_id,
            title=task_title,
            metadata=meta,  # context + field diffs
            actor_display=user_id,
        )
    return result


async def delete_task_attachment(
    attachment_id: str,
    username: Optional[str] = None,
    soft_delete: bool = False,
    task_title: Optional[str] = None,
) -> Dict[str, Any]:
    current = await get_task_attachment(attachment_id)
    if not current or not current.data:
        raise HTTPException(status_code=404, detail="Attachment not found")
    att = current.data[0] if isinstance(current.data, list) else current.data

    sb = get_supabase_client()
    # Do not delete from storage; only remove DB row or mark as deleted in table

    if soft_delete:
        delete_data = {
            "deleted_at": datetime.datetime.utcnow().replace(microsecond=0).isoformat(),
            "deleted_by": username,
        }
        def op():
            return sb.from_("task_attachments").update(delete_data).eq("attachment_id", attachment_id).execute()
    else:
        def op():
            return sb.from_("task_attachments").delete().eq("attachment_id", attachment_id).execute()

    result = await safe_supabase_operation(op, "Failed to delete task attachment")

    if username:
        await record_history(
            task_id=att["task_id"],
            action="attachment_deleted",
            created_by=username,
            title=task_title,
            metadata={
                "attachment_id": att.get("attachment_id"),
                "filename": att.get("name") or att.get("filename"),
                "url": att.get("url"),
            },
            actor_display=None,
        )
    return result


async def list_task_attachments(task_id: str):
    sb = get_supabase_client()
    def op():
        return (
            sb.from_("task_attachments")
            .select("*")
            .eq("task_id", task_id)
            .is_("deleted_at", None)
            # .is_("is_inline", None)  # Only list non-inline attachments
            .or_("is_inline.is.false,is_inline.is.null")
            .order("uploaded_at", desc=True)
            .execute()
        )
    return await safe_supabase_operation(op, "Failed to list attachments")
