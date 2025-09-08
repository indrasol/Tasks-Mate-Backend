from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from typing import Optional, List
from app.services.organization_service import _organization_exists

async def create_designation(data: dict):
    org_id = data.get("org_id")
    role = data.get("role")
    if not org_id or not role:
        raise ValueError("org_id and role are required")
    
    if not await _organization_exists(org_id):
        raise ValueError("Organization does not exist")
    
    # Generate designation ID: "D" followed by 4 random digits
    import random
    designation_id = f"D{random.randint(1000, 9999)}"
    data["designation_id"] = designation_id
    
    supabase = get_supabase_client()
    def op():
        return supabase.from_("designations").insert(data).execute()
    create_result = await safe_supabase_operation(op, "Failed to create designation")

    # --- Keep organization's designations column in sync
    # Fetch existing designations array and append if missing
    supabase = get_supabase_client()
    designation_name = data.get("name")
    if designation_name:
        def org_op():
            return supabase.from_("organizations").select("designations").eq("org_id", org_id).single().execute()

        org_result = await safe_supabase_operation(org_op, "Failed to fetch organization designations")
        current_designations: List[str] = org_result.data.get("designations") or []
        if designation_name not in current_designations:
            updated = current_designations + [designation_name]
            def upd_op():
                return supabase.from_("organizations").update({"designations": updated}).eq("org_id", org_id).execute()
            await safe_supabase_operation(upd_op, "Failed to update organization designations")

    return create_result

async def get_designation(designation_id: str):
    supabase = get_supabase_client()
    def op():
        return supabase.from_("designations").select("*").eq("designation_id", designation_id).single().execute()
    return await safe_supabase_operation(op, "Failed to fetch designation")

async def get_designations(org_id: Optional[str] = None):
    """Fetch all designations. If org_id is provided, filter by that organization."""
    supabase = get_supabase_client()
    def op():
        query = supabase.from_("designations").select("*")
        if org_id:
            query = query.eq("org_id", org_id)
        # Add ordering to ensure consistent results
        return query.order("name").execute()
    result = await safe_supabase_operation(op, "Failed to fetch designations")
    
    # Remove duplicates based on name (case-insensitive) at the backend level
    if result.data:
        seen_names = set()
        unique_designations = []
        for designation in result.data:
            name_lower = designation.get("name", "").lower()
            if name_lower not in seen_names:
                seen_names.add(name_lower)
                unique_designations.append(designation)
        result.data = unique_designations
    
    return result

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