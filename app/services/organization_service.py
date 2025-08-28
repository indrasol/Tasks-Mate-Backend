import datetime
from typing import Optional, Union, List
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from app.models.enums import RoleEnum
from app.services.utils import inject_audit_fields

async def _generate_sequential_org_id() -> str:
    """Generate the next sequential organization ID in the format 'O0001'.
    The numeric portion is strictly increasing even if organizations are
    deleted, as we always look at the current maximum and increment it.
    """
    supabase = get_supabase_client()

    def op():
        # Because the numeric part is zero-padded, ordering by the full string
        # gives us the highest numeric value as well.
        return (
            supabase
            .from_("organizations")
            .select("org_id")
            .order("org_id", desc=True)
            .limit(1)
            .execute()
        )

    res = await safe_supabase_operation(op, "Failed to fetch last organization id")
    last_id: Optional[str] = None
    if res and res.data:
        last_id = res.data[0]["org_id"]

    last_num = 0
    if last_id and isinstance(last_id, str) and last_id.startswith("O"):
        try:
            last_num = int(last_id[1:])
        except ValueError:
            last_num = 0

    next_num = last_num + 1
    # Pad with at least 4 digits (O0001, O0010, etc.) but grow automatically
    return f"O{next_num:04d}"


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


async def _organization_name_exists(name: str, username:str, email:str) -> bool:
    supabase = get_supabase_client()
    result = supabase.from_("organizations").select("org_id").eq("name", name).execute()

    # loop through result.data and check if any org_id matches the membership
    for org in result.data:
        result = supabase.from_("organization_members").select("org_id").eq("org_id", org["org_id"]).eq("email", email).eq("is_active", True).limit(1).execute()
        if(bool(result.data)):
            return True

    # loop through result.data and check if any invite is present
    for org in result.data:
        result = supabase.from_("organization_invites").select("org_id").eq("org_id", org["org_id"]).eq("email", email).eq("invite_status", "pending").limit(1).execute()
        if(bool(result.data)):
            return True
            
    return False


async def create_organization(data: dict):
    """Create an organization and make sure its `designations` column is populated.

    Steps:
    1. Generate organization ID in format "O{random 6 digit number}"
    2. Validate & deduplicate incoming `designations` in data (if any).
    3. Fetch the list of *global* designations (rows whose `org_id` is NULL).
    4. Combine → unique(defaults + incoming_custom).
    5. Persist this combined array when inserting into `organizations` table.
    """
    _validate_data(data, required_fields=["name","description"])
    name = data["name"]
    created_by = data["created_by"]
    created_by_email = data["created_by_email"]

    #remove created_by_email from data
    data.pop("created_by_email", None)

    # Prevent duplicates on name
    if await _organization_name_exists(name, created_by, created_by_email):
        raise ValueError(f"Organization with name '{name}' already exists.")
    
    # Generate sequential organization ID e.g. 'O0001', 'O0002', ...
    org_id = await _generate_sequential_org_id()
    # In the rare case of a race condition generating a duplicate, retry a few times
    attempts = 0
    while await _organization_exists(org_id):
        attempts += 1
        if attempts > 5:
            raise RuntimeError("Unable to generate a unique organization id after multiple attempts")
        org_id = await _generate_sequential_org_id()
    data["org_id"] = org_id

    # 1. Prepare designation list coming from client (may be missing)
    incoming_designations: List[str] = []

    # Support single 'designation' field
    single_designation = data.pop("designation", None)
    if single_designation and isinstance(single_designation, str):
        incoming_designations.append(single_designation.strip())

    # Import here to avoid circular dependencies
    from app.services.designation_service import get_designations
    # 2. Fetch global defaults
    default_res = await get_designations(org_id=None)
    default_designations = [row["name"] for row in (default_res.data or [])]

    # 3. Merge & deduplicate
    all_designations = list({*default_designations, *incoming_designations})

    # 4. Persist
    data["designations"] = all_designations

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


async def get_organization_name(org_id: str):
    _validate_org_id(org_id)
    supabase = get_supabase_client()

    def op():
        return supabase.from_("organizations").select("name").eq("org_id", org_id).single().execute()

    return await safe_supabase_operation(op, "Failed to fetch organization")


async def update_organization(org_id: str, data: dict):
    """Update an organization record with additional safeguards.

    • Validates input and existence.
    • Prevents duplicate org names when changing the name.
    • Automatically injects an updated_at timestamp if not supplied.
    """
    _validate_org_id(org_id)
    _validate_data(data)

    # Check if org exists before attempting update
    supabase = get_supabase_client()
    existing_res = supabase.from_("organizations").select("name").eq("org_id", org_id).single().execute()
    if not existing_res.data:
        raise ValueError(f"Cannot update: Organization '{org_id}' does not exist.")

    current_name = existing_res.data.get("name") if existing_res.data else None

    # If the user is attempting to change the name, ensure the new name is unique
    new_name = data.get("name")
    updated_by = data.get("updated_by")
    updated_by_email = data.get("updated_by_email")

    # remove updated_by_email from data
    data.pop("updated_by_email", None)

    if new_name and new_name != current_name:
        if await _organization_name_exists(new_name, updated_by, updated_by_email):
            raise ValueError(f"Organization name '{new_name}' is already in use. Please choose a different name.")

    # Auto-set updated_at timestamp if not provided
    data.setdefault("updated_at", datetime.datetime.utcnow().isoformat())

    def op():
        return supabase.from_("organizations").update(data).eq("org_id", org_id).execute()

    return await safe_supabase_operation(op, "Failed to update organization")


async def delete_organization(org_id: str, metadata: Optional[dict] = None):
    _validate_org_id(org_id)

    if not await _organization_exists(org_id):
        raise ValueError(f"Cannot delete: Organization '{org_id}' does not exist.")

    if not metadata or "deleted_by" not in metadata:
        raise ValueError("Missing required metadata: 'deleted_by'")

    supabase = get_supabase_client()

    def op():
        try:
            # Step 1: Fetch existing org record
            response = supabase.table("organizations").select("*").eq("org_id", org_id).single().execute()
            org_data = response.data  # this will raise if query fails

            if not org_data:
                raise Exception(f"Organization '{org_id}' not found.")

            # Step 2: Add delete metadata
            if metadata and metadata.get("delete_reason"):
                org_data["delete_reason"] = metadata["delete_reason"]
            org_data["deleted_by"] = metadata.get("deleted_by", "unknown")
            org_data["deleted_at"] = datetime.datetime.utcnow().isoformat()

            # Step 3: Insert into organizations_history
            supabase.table("organizations_history").insert(org_data).execute()

            # Step 4: Delete from organizations
            supabase.table("organizations").delete().eq("org_id", org_id).execute()

            return {"status": "deleted", "org_id": org_id}

        except Exception as e:
            raise Exception(f"Supabase operation failed: {str(e)}")

    # Run safely
    return await safe_supabase_operation(op, "Failed to delete organization")


async def get_organizations_for_user(user_id: str, username: str, email: Optional[str] = None, org_id: Optional[str] = None) -> List[dict]:
    """
    Get organizations for a user and return them as OrgCard format objects
    with role and designation information.
    """
    _validate_user_id(user_id)
    _validate_email(email)

    supabase = get_supabase_client()

    # Get orgs where user is a member with role and designation
    def member_op():
        if org_id:
            return supabase.from_("organization_members").select("org_id, role, designation").eq("user_id", user_id).eq("org_id",org_id).execute()
        else:             
            return supabase.from_("organization_members").select("org_id, role, designation").eq("user_id", user_id).execute()

    member_result = await safe_supabase_operation(member_op, "Failed to fetch organization memberships")
    
    # Create a map of org_id to member info (role and designation)
    member_info = {}
    member_org_ids = set()
    
    for row in member_result.data or []:
        org_id = row["org_id"]
        member_org_ids.add(org_id)
        member_info[org_id] = {
            "role": row.get("role", "member"),
            "designation": row.get("designation")
        }

    # Handle invites if email provided
    invite_org_ids = set()
    if email:
        def invite_op():
            return supabase.from_("organization_invites").select("org_id, id").eq("email", email).execute()

        invite_result = await safe_supabase_operation(invite_op, "Failed to fetch organization invites")
        invite_org_ids = {row["org_id"] for row in invite_result.data or []}

    only_invite_org_ids = invite_org_ids - member_org_ids
    all_org_ids = member_org_ids #| only_invite_org_ids

    if not all_org_ids:
        return []

    # Fetch organization info with project and member counts from the new view
    def orgs_op():
        return supabase.from_("organization_stats_view").select("org_id, org_name, org_description, created_by, created_at, project_count, member_count").in_("org_id", list(all_org_ids)).execute()

    orgs_result = await safe_supabase_operation(orgs_op, "Failed to fetch organizations with stats")
    
    # If the view query fails, fall back to basic organization info
    if not orgs_result.data:
        def fallback_op():
            return supabase.from_("organizations").select("org_id, name, created_by, created_at, description").in_("org_id", list(all_org_ids)).execute()
        
        orgs_result = await safe_supabase_operation(fallback_op, "Failed to fetch organizations")
    
    orgs = orgs_result.data or []

    # Convert to OrgCard format
    org_cards = []
    for org in orgs:
        org_id = org.get("org_id")
        
        # Get role and designation from member_info
        role = "member"  # Default
        designation = None
        
        if org_id in member_info:
            role = member_info[org_id]["role"]
            designation = member_info[org_id]["designation"]

        invitation_id = None
        is_invite = False

        if org_id in only_invite_org_ids:
            is_invite = True
            # get id based on org_id
            # invitation_id = next((m.id for m in invite_result.data if m.org_id == org_id), None)        
            invitation_id = next((m["id"] for m in invite_result.data if m["org_id"] == org_id), None)

        
        # Create OrgCard dict
        org_card = {
            "org_id": org_id,
            "name": org.get("org_name", ""),
            "description": org.get("org_description", ""),
            "role": role,
            "created_by": org.get("created_by", ""),
            "created_at": org.get("created_at", ""),
            "designation": designation,
            "project_count": org.get("project_count", 0),
            "member_count": org.get("member_count", 0),
            "is_invite":is_invite,
            "invitation_id": invitation_id
        }
        
        org_cards.append(org_card)

    return org_cards
