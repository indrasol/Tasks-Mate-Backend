from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from fastapi import HTTPException
from typing import Optional
import time, re

# Cache designations in-process for a short period to avoid frequent DB hits
_DESIGNATION_CACHE: tuple[list[dict], float] | None = None  # (rows, timestamp)
_CACHE_TTL = 60  # seconds


async def _get_designations_cached():
    global _DESIGNATION_CACHE
    now = time.time()
    if _DESIGNATION_CACHE and now - _DESIGNATION_CACHE[1] < _CACHE_TTL:
        return _DESIGNATION_CACHE[0]

    supabase = get_supabase_client()

    def op():
        return (
            supabase
            .from_("designations")
            .select("name,slug,metadata")
            .execute()
        )

    res = await safe_supabase_operation(op, "Failed to fetch designations list")
    rows = res.data or []
    _DESIGNATION_CACHE = (rows, now)
    return rows


def _acronym(text: str) -> str:
    return "".join(word[0] for word in re.split(r"[^A-Za-z]+", text) if word).lower()


async def _resolve_designation_slug(raw: str) -> Optional[str]:
    """Return the slug for a given designation display-name/slug.

    Looks up the `designations` table for either a matching `name` or
    `slug` (case-insensitive). Returns the slug string if found, else
    None.
    """
    if not raw:
        return None

    rows = await _get_designations_cached()

    raw_lower = raw.lower().strip()

    # Exact name match (case-insensitive)
    for r in rows:
        if str(r.get("name", "")).lower() == raw_lower:
            return r.get("slug")

    # Exact slug match
    for r in rows:
        if str(r.get("slug", "")).lower() == raw_lower:
            return r.get("slug")

    # Match metadata.slug
    for r in rows:
        meta_slug = (r.get("metadata") or {}).get("slug") if isinstance(r.get("metadata"), dict) else None
        if meta_slug and meta_slug.lower() == raw_lower:
            return r.get("slug")

    # Try slugified candidate
    candidate = re.sub(r"[^A-Za-z0-9]+", "_", raw).lower().strip("_")
    if candidate:
        for r in rows:
            if r.get("slug") == candidate:
                return candidate

    # Try acronym (e.g., Chief Technology Officer -> cto)
    acr = _acronym(raw)
    if acr:
        for r in rows:
            if r.get("slug") == acr:
                return acr

    return None


async def _resolve_slug_to_name(slug: str) -> Optional[str]:
    """Return the display name for a given designation slug.
    
    Looks up the `designations` table for a matching `slug` and returns
    the `name` field if found.
    """
    if not slug:
        return None

    rows = await _get_designations_cached()

    for r in rows:
        if r.get("slug") == slug:
            return r.get("name")

    return None


async def check_project_member_exists(data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_members").select("user_id").eq("project_id", data["project_id"]).eq("user_id",  data["user_id"]).limit(1).execute()
    res = await safe_supabase_operation(op, "Failed to check project member exists")
    if res.data:
        raise HTTPException(400, detail="User already belongs to this project")

async def create_project_member(data: dict):
    supabase = get_supabase_client()

    # Normalize designation to valid slug if provided
    if data.get("designation"):
        resolved = await _resolve_designation_slug(data["designation"])
        if not resolved:
            # If resolution fails, check if it's a special case like "Organization Owner"
            # and provide a fallback
            designation_lower = data["designation"].lower().strip()
            if "organization" in designation_lower and "owner" in designation_lower:
                # Use "manager" as fallback for organization owners in project context
                data["designation"] = "manager"
            else:
                raise HTTPException(400, detail=f"Invalid designation provided: {data['designation']}")
        else:
            data["designation"] = resolved

    await check_project_member_exists(data)

    def op():
        return supabase.from_("project_members").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to create project member")

async def get_project_member(user_id: str, project_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_members").select("*").eq("user_id", user_id).eq("project_id", project_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch project member")

async def update_project_member(user_id: str, project_id: str, data: dict):
    # Normalize designation to valid slug if provided
    if data.get("designation"):
        resolved = await _resolve_designation_slug(data["designation"])
        if not resolved:
            # If resolution fails, check if it's a special case like "Organization Owner"
            # and provide a fallback
            designation_lower = data["designation"].lower().strip()
            if "organization" in designation_lower and "owner" in designation_lower:
                # Use "manager" as fallback for organization owners in project context
                data["designation"] = "manager"
            else:
                raise HTTPException(400, detail=f"Invalid designation provided: {data['designation']}")
        else:
            data["designation"] = resolved
    
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_members").update(data).eq("user_id", user_id).eq("project_id", project_id).execute()
    return await safe_supabase_operation(op, "Failed to update project member")

async def delete_project_member(user_id: str, project_id: str, metadata: dict | None = None):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("project_members").delete().eq("user_id", user_id).eq("project_id", project_id).execute()
    return await safe_supabase_operation(op, "Failed to delete project member")

async def get_members_for_project(project_id, search=None, limit=20, offset=0, sort_by="updated_at", sort_order="asc", role=None):
    supabase = get_supabase_client()
    query = supabase.from_("project_members").select("*").eq("project_id", project_id)
    # if search:
    #     query = query.ilike("user_name", f"%{search}%")
    if role:
        query = query.eq("role", role)
    query = query.order(sort_by, desc=(sort_order == "desc"))
    result = query.range(offset, offset + limit - 1).execute()
    
    # Convert designation slugs back to display names for frontend
    members = result.data or []
    for member in members:
        if member.get("designation"):
            display_name = await _resolve_slug_to_name(member["designation"])
            if display_name:
                member["designation"] = display_name
    
    return members