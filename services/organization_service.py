from typing import Optional, Union, List
from core.db.supabase_db import get_supabase_client, safe_supabase_operation


def _validate_org_id(org_id: str):
    if not org_id or not isinstance(org_id, str) or not org_id.strip():
        raise ValueError("Invalid 'org_id'. It must be a non-empty string.")
    if len(org_id) > 64:
        raise ValueError("'org_id' must be 64 characters or less.")


def _validate_user_id(user_id: str):
    if not user_id or not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("Invalid 'user_id'. It must be a non-empty string.")


def _validate_email(email: Optional[str]):
    if email is not None and (not isinstance(email, str) or "@" not in email or not email.strip()):
        raise ValueError("Invalid email address provided.")


def _validate_data(data: dict, required_fields: Optional[List[str]] = None):
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary.")
    if required_fields:
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(f"Missing required fields in data: {', '.join(missing)}")


async def _organization_exists(org_id: str) -> bool:
    supabase = get_supabase_client()
    result = supabase.from_("organizations").select("org_id").eq("org_id", org_id).execute()
    return bool(result.data)


async def _organization_name_exists(name: str) -> bool:
    supabase = get_supabase_client()
    result = supabase.from_("organizations").select("org_id").eq("name", name).execute()
    return bool(result.data)


async def create_organization(data: dict):
    _validate_data(data, required_fields=["name"])
    # _validate_org_id(data["org_id"])
    # org_id = data["org_id"]
    name = data["name"]

    # if await _organization_exists(org_id):
    #     raise ValueError(f"Organization with org_id '{org_id}' already exists.")

    if await _organization_name_exists(name):
        raise ValueError(f"Organization with name '{name}' already exists.")

    supabase = get_supabase_client()

    def op():
        return supabase.from_("organizations").insert(data).execute()

    return await safe_supabase_operation(op, "Failed to create organization")


async def get_organization(org_id: str):
    _validate_org_id(org_id)
    supabase = get_supabase_client()

    def op():
        return supabase.from_("organizations").select("*").eq("org_id", org_id).single().execute()

    return await safe_supabase_operation(op, "Failed to fetch organization")


async def update_organization(org_id: str, data: dict):
    _validate_org_id(org_id)
    _validate_data(data)

    # Check if org exists before attempting update
    if not await _organization_exists(org_id):
        raise ValueError(f"Cannot update: Organization '{org_id}' does not exist.")

    supabase = get_supabase_client()

    def op():
        return supabase.from_("organizations").update(data).eq("org_id", org_id).execute()

    return await safe_supabase_operation(op, "Failed to update organization")


async def delete_organization(org_id: str):
    _validate_org_id(org_id)

    if not await _organization_exists(org_id):
        raise ValueError(f"Cannot delete: Organization '{org_id}' does not exist.")

    supabase = get_supabase_client()

    def op():
        return supabase.from_("organizations").delete().eq("org_id", org_id).execute()

    return await safe_supabase_operation(op, "Failed to delete organization")


async def get_organizations_for_user(user_id: str, email: Optional[str] = None) -> Union[List[dict], list]:
    _validate_user_id(user_id)
    _validate_email(email)

    supabase = get_supabase_client()

    # Get orgs where user is a member
    def member_op():
        return supabase.from_("organization_members").select("org_id").eq("user_id", user_id).execute()

    member_result = await safe_supabase_operation(member_op, "Failed to fetch organization memberships")
    member_org_ids = {row["org_id"] for row in member_result.data or []}

    invite_org_ids = set()
    if email:
        def invite_op():
            return supabase.from_("organization_invites").select("org_id").eq("email", email).execute()

        invite_result = await safe_supabase_operation(invite_op, "Failed to fetch organization invites")
        invite_org_ids = {row["org_id"] for row in invite_result.data or []}

    only_invite_org_ids = invite_org_ids - member_org_ids
    all_org_ids = member_org_ids | only_invite_org_ids

    if not all_org_ids:
        return []

    def orgs_op():
        return supabase.from_("organizations").select("*").in_("org_id", list(all_org_ids)).execute()

    orgs_result = await safe_supabase_operation(orgs_op, "Failed to fetch organizations")
    orgs = orgs_result.data or []

    for org in orgs:
        org_id = org.get("org_id")
        if org_id in member_org_ids:
            org["access_status"] = "member"
        elif org_id in only_invite_org_ids:
            org["access_status"] = "invite"
        else:
            org["access_status"] = "unknown"

    return orgs
