from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation

async def create_designation(data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("designations").insert(data).execute()
    return await safe_supabase_operation(op, "Failed to create designation")

async def get_designation(designation_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("designations").select("*").eq("designation_id", designation_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch designation")

async def update_designation(designation_id: str, data: dict):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("designations").update(data).eq("designation_id", designation_id).execute()
    return await safe_supabase_operation(op, "Failed to update designation")

async def delete_designation(designation_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("designations").delete().eq("designation_id", designation_id).execute()
    return await safe_supabase_operation(op, "Failed to delete designation")