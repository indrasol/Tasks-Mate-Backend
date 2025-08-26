import unicodedata
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation

import datetime

import os
import re
import mimetypes
from typing import Dict, Any, Optional
from fastapi import HTTPException, UploadFile

import urllib.parse

# Storage bucket for project resources
RESOURCES_BUCKET = os.getenv("PROJECT_RESOURCES_BUCKET", "project-resources")

def _extract_public_url(url_result: Any) -> str:
	if isinstance(url_result, dict):
		data = url_result.get("data") or {}
		return data.get("publicUrl") or data.get("public_url") or ""
	if isinstance(url_result, str):
		return url_result
	maybe = getattr(url_result, "public_url", None) or getattr(url_result, "publicUrl", None)
	return str(maybe or "")

def _guess_content_type(filename: str, fallback: str = "application/octet-stream") -> str:
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

def _safe_storage_path(project_id: str, original: str, existing: Optional[set[str]]) -> str:
	# Be defensive in case caller passes None
	existing = existing or set()
	base, dot, ext = original.rpartition(".")
	if not base:
		base, ext, dot = original, "", ""
	path = f"{project_id}/{original}"
	i = 1
	while path in existing:
		candidate = f"{base}_{i}{dot}{ext}" if ext else f"{base} ({i})"
		path = f"{project_id}/{candidate}"
		i += 1
	return path

async def _list_existing_paths(sb, project_id: str) -> set[str]:
	try:
		listing = sb.storage.from_(RESOURCES_BUCKET).list(path=project_id)

		# Coerce to a list of item dicts
		if isinstance(listing, dict):
			data = listing.get("data") or listing.get("body") or listing.get("items") or []
		else:
			data = getattr(listing, "data", None) or listing
		if not isinstance(data, list):
			data = []

		names = []
		for o in data:
			if isinstance(o, dict):
				name = o.get("name") or o.get("path") or o.get("Name")
			else:
				name = getattr(o, "name", None) or getattr(o, "path", None)
			if name:
				names.append(str(name).lstrip("/"))

		return {f"{project_id}/{n}" for n in names if n}
	except Exception as e:
		return set()

# def _sanitize_name(name: str) -> str:
# 	name = name.replace("\\", "/").split("/")[-1]
# 	return re.sub(r"[^A-Za-z0-9 ._\-()]", "_", name)[:255]

def _sanitize_name(name: str) -> str:
	# Drop any directory components
	raw = (name or "file").replace("\\", "/").split("/")[-1]
	# Decode percent-encoding (e.g., %20)
	raw = urllib.parse.unquote(raw)
	# Normalize unicode (compatibility form)
	raw = unicodedata.normalize("NFKC", raw)
	# Remove non-printable/control chars
	raw = "".join(ch for ch in raw if ch.isprintable())
	# Restrict to safe set
	safe = re.sub(r"[^A-Za-z0-9 ._\-()]", "_", raw)
	# Collapse whitespace and trim leading/trailing spaces/dots
	safe = re.sub(r"[ \t]+", " ", safe).strip(" .")
	# Default if empty
	if not safe:
		safe = "file"
	# Max filename length
	return safe[:255]

async def _generate_sequential_resource_id() -> str:
    """Generate next sequential id like 'RE0001'"""
    supabase = get_supabase_client()
    def op():
        return (
            supabase.from_("project_resources")
            .select("resource_id")
            .order("resource_id", desc=True)
            .limit(1)
            .execute()
        )
    res = await safe_supabase_operation(op, "Failed to fetch last resource id")
    last = res.data[0]["resource_id"] if res and res.data else None
    last_num = 0
    if last and isinstance(last, str) and last.startswith("RE"):
        try:
            last_num = int(last[2:])
        except ValueError:
            last_num = 0
    return f"RE{last_num+1:04d}"

async def create_project_resource(data: dict):

    print(f"Creating project resource: {data}")
    # Map flexible keys
    if "name" in data and "resource_name" not in data:
        data["resource_name"] = data.pop("name")
    if "url" in data and "resource_url" not in data:
        data["resource_url"] = data.pop("url")

    # Fetch project_name if not provided
    if "project_id" in data and "project_name" not in data:
        try:
            proj_sb = get_supabase_client()
            proj_res = proj_sb.from_("projects").select("name").eq("project_id", data["project_id"]).single().execute()
            if proj_res and proj_res.data and proj_res.data.get("name"):
                data["project_name"] = proj_res.data["name"]
        except Exception:
            pass

    if "resource_id" not in data:
        data["resource_id"] = await _generate_sequential_resource_id()

    if "created_at" not in data:
        data["created_at"] = datetime.datetime.utcnow().isoformat()

    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_resources").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to create project resource")

async def get_project_resource(resource_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_resources").select("*").eq("resource_id", resource_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch project resource")

async def update_project_resource(resource_id: str, data: dict):
    if "name" in data and "resource_name" not in data:
        data["resource_name"] = data.pop("name")
    if "url" in data and "resource_url" not in data:
        data["resource_url"] = data.pop("url")
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_resources").update(data).eq("resource_id", resource_id).execute()
    return await safe_supabase_operation(op, "Failed to update project resource")

async def delete_project_resource(resource_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_resources").delete().eq("resource_id", resource_id).execute()
    return await safe_supabase_operation(op, "Failed to delete project resource")

async def get_resources_for_project(project_id, search=None, limit=20, offset=0, sort_by="resource_type", sort_order="asc", resource_type=None):
    supabase = get_supabase_client()
    query = supabase.from_("project_resources").select("*").eq("project_id", project_id)
    if search:
        query = query.ilike("resource_type", f"%{search}%")
    if resource_type:
        query = query.eq("resource_type", resource_type)
    query = query.order(sort_by, desc=(sort_order == "desc"))
    result = query.range(offset, offset + limit - 1).execute()
    return result.data

async def upload_and_create_project_resource(
    *,
    project_id: str,
    project_name:  Optional[str],
    file: UploadFile,
    title: Optional[str],
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    actor_display: Optional[str] = None
) -> Dict[str, Any]:
    """
    - Enforce per-task limit
    - Generate sequential id A0001...
    - Upload to storage: {task_id}/{original_filename}
    - Fetch public URL
    - Create DB row with the public URL
    - Log 'attachment_created'
    """
    
    sb = get_supabase_client()
    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat()

    # 1) Generate ID & storage path
    # attachment_id = await _generate_sequential_attachment_id()
    # attachment_id = await _next_attachment_id_retry(sb)
    # original_name = file.filename
    original_name = _sanitize_name(title or file.filename or "file")
    storage_path = f"{project_id}/{original_name}"

    # 2) Upload to storage
    # Note: use upsert=False to avoid overwriting; you can switch to True if desired
    try:
        # Ensure unique storage path under this task
        existing = await _list_existing_paths(sb, project_id)
        storage_path = _safe_storage_path(project_id, original_name, existing)

        # Read the uploaded file as bytes to satisfy clients that don't accept SpooledTemporaryFile
        file_bytes = await file.read()

        # Choose the best content type available
        content_type = _guess_content_type(original_name)
        if content_type in ("application/octet-stream", "text/plain"):
            # Try by extension when generic or plain text
            content_type = _guess_content_type(original_name, fallback="application/octet-stream")

        sb.storage.from_(RESOURCES_BUCKET).upload(
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
        encoded_path = urllib.parse.quote(storage_path)
        url_result = sb.storage.from_(RESOURCES_BUCKET).get_public_url(encoded_path)
        
        public_url = _extract_public_url(url_result)
        if not public_url:
            raise RuntimeError("Empty public URL from storage")
        else:
            public_url = public_url.rstrip("?")
    except Exception as e:
        # attempt cleanup (best effort)
        try:
            sb.storage.from_(RESOURCES_BUCKET).remove([storage_path])
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to get public URL: {e}")

    # 4) Insert DB row
    row = {
        "project_id": project_id,
        "project_name": project_name,
        # store both for backward compatibility
        "storage_path": storage_path,
        "resource_name": original_name,
        "resource_url": public_url,
        "resource_type": 'file',
        "created_by": username,
        "created_at": now,
    }

    return await create_project_resource(row)