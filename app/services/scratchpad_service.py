from typing import Any, Dict

from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation


async def get_scratchpad(org_id: str, user_id: str):
    supabase = get_supabase_client()

    def op():
        return (
            supabase
            .from_("scratchpads")
            .select("*")
            .eq("org_id", org_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )

    return await safe_supabase_operation(op, "Failed to fetch scratchpad")


async def upsert_scratchpad(data: Dict[str, Any]):
    """Insert or update a scratchpad entry based on (org_id,user_id) composite key"""
    supabase = get_supabase_client()

    def op():
        return (
            supabase
            .from_("scratchpads")
            .upsert(data)
            .execute()
        )

    return await safe_supabase_operation(op, "Failed to upsert scratchpad")
