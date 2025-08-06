
from typing import List
import uuid
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from app.models.schemas.project import ProjectCard

import datetime


async def get_user_details_by_id(user_id: str):
    """Fetch a single username from the users table for the given user_id."""
    supabase = get_supabase_client()
    def op():
        return (
            supabase
            .from_("users")
            .select("*")
            .eq("id", user_id)
            .single()
            .execute()
        )
    result = await safe_supabase_operation(op, "Failed to fetch username")
    user_details = {}
    if result and result.data:
        user_details["username"] = result.data["username"]
        user_details["email"] = result.data["email"]
        user_details["id"] = result.data["id"]
    return user_details

async def get_user_details_by_username(username: str):
    """Fetch a single username from the users table for the given user_id."""
    supabase = get_supabase_client()
    def op():
        return (
            supabase
            .from_("users")
            .select("*")
            .eq("username", username)
            .single()
            .execute()
        )
    result = await safe_supabase_operation(op, "Failed to fetch username")
    user_details = {}
    if result and result.data:
        user_details["username"] = result.data["username"]
        user_details["email"] = result.data["email"]
        user_details["id"] = result.data["id"]
    return user_details
