from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from app.services.utils import inject_audit_fields

from app.utils.logger import get_logger

logger = get_logger()

import datetime
from fastapi import HTTPException
from typing import Optional
# Designation utilities
from app.core.db.supabase_db import get_supabase_client

# Cache designations in-process for a short period to avoid frequent DB hits
_DESIGNATION_CACHE: tuple[list[dict], float] | None = None  # (rows, timestamp)
_CACHE_TTL = 60  # seconds

import time, re


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

async def check_organization_member_exists(data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("organization_members").select("user_id").eq("org_id", data["org_id"]).ilike("email", data["email"]).eq("is_active", True).limit(1).execute()
    res = await safe_supabase_operation(op, "Failed to check organization member exists")
    if res.data:
        raise HTTPException(400, detail="User is already a member of this organization")

async def create_organization_member(data: dict):
    supabase = get_supabase_client()
    # Ensure invited_at timestamp
    now_iso = datetime.datetime.utcnow().isoformat()
    data.setdefault("invited_at", now_iso)
    # Auto-accept for owners (initial creator) if not provided
    if data.get("role") == "owner":
        data.setdefault("accepted_at", now_iso)
        # Always set "Organization Owner" designation for owners
        owner_slug = await _resolve_designation_slug("Organization Owner")
        data["designation"] = owner_slug or "organization_owner"
    else:
        # For non-owners, normalize designation to valid slug if provided
        # If no designation provided, leave it as None/null for placeholder display
        if data.get("designation"):
            resolved = await _resolve_designation_slug(data["designation"])
            if not resolved:
                raise HTTPException(400, detail="Invalid designation provided")
            data["designation"] = resolved
        else:
            # Explicitly set to None for members without designation
            data["designation"] = None

    await check_organization_member_exists(data)

    def op():
        return supabase.from_("organization_members").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to create organization member")

async def get_organization_member(user_id: str, org_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("organization_members").select("*").eq("user_id", user_id).eq("org_id", org_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch organization member")

async def update_organization_member(user_id: str, org_id: str, data: dict):
    # Normalize designation to valid slug if provided
    if data.get("designation"):
        resolved = await _resolve_designation_slug(data["designation"])
        if not resolved:
            raise HTTPException(400, detail="Invalid designation provided")
        data["designation"] = resolved
    
    supabase = get_supabase_client()
    def op():
        # data = inject_audit_fields(data,None,"update")
        return supabase.from_("organization_members").update(data).eq("user_id", user_id).eq("org_id", org_id).execute()
    return await safe_supabase_operation(op, "Failed to update organization member")

async def delete_organization_member(user_id: str, org_id: str, data:dict):
    supabase = get_supabase_client()
    def op():
        # data = inject_audit_fields(data,None,"delete")
        return supabase.from_("organization_members").delete().eq("user_id", user_id).eq("org_id", org_id).execute()
    return await safe_supabase_operation(op, "Failed to delete organization member")

async def get_members_for_org(org_id, search=None, limit=20, offset=0, sort_by="updated_at", sort_order="asc", role=None, is_active=None):
    supabase = get_supabase_client()
    # logger.info("Fetching members for org_id=%s", org_id)
    query = supabase.from_("organization_members").select("*").eq("org_id", org_id).eq("is_active", True)
    # if search:
    #     query = query.ilike("designation", f"%{search}%")
    if role:
        query = query.eq("role", role)
    # if is_active is not None:
    #     query = query.eq("is_active", is_active)
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