from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.api.v1.routes.organizations.org_rbac import org_rbac
from app.api.v1.routes.projects.proj_rbac import project_rbac
from app.models.enums import RoleEnum
from app.models.schemas.project import ProjectCard, ProjectCreate, ProjectUpdate, ProjectInDB
from app.services.project_service import create_project, get_project, update_project, delete_project, get_projects_for_user, get_project_card, get_all_org_projects
from app.services.auth_handler import verify_token
from app.services.rbac import get_project_role
from app.services.project_member_service import create_project_member
from app.services.role_service import create_role, get_role_by_name
from app.services.utils import inject_audit_fields
from app.services.user_service import get_user_details_by_id
from app.core.db.supabase_db import get_supabase_client

router = APIRouter()



@router.post("", response_model=ProjectCard)
async def create_project_route(project: ProjectCreate, user=Depends(verify_token), org_role=Depends(org_rbac)):
    """Create a project and immediately return a fully-hydrated `ProjectCard` instance."""
    # Only organization owner/admin can create projects
    if not org_role:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Inject audit fields – we want `created_by` to store the username rather than the raw user_id
    data = inject_audit_fields(
        project.dict(),
        user["username"],
        action="create_proj",
    )
    
    # Ensure org_id is present (it comes from query/body – pydantic schema enforces)
    # If the frontend hasn't supplied it, raise a clear error
    if not data.get("org_id"):
        raise HTTPException(status_code=400, detail="Missing org_id in request body")

    # Persist the project
    result = await create_project(data)
    project_id = result.data[0]["project_id"]

    # Determine the project owner sent by client; fall back to creator
    owner_identifier = project.owner or user["id"]

    # Ensure OWNER role exists
    role_res = await get_role_by_name(RoleEnum.OWNER.value)
    if role_res.data:
        owner_role = role_res.data[0]["name"]

    already_added: set[str] = set()

    # Resolve owner details by ID or username; store username in projects table
    user_details = await get_user_details_by_id(owner_identifier)
    if user_details and user_details.get("username"):
        data["owner"] = user_details["username"]

    # Insert owner membership with designation if provided
    owner_designation = project.dict().get("owner_designation", "")
    
    # Get the owner's name instead of ID
    owner_username = user_details.get("username", "")
    
    # Store owner's username in the project data
    # This ensures the 'owner' column has the username instead of ID
    if user_details and user_details.get("username"):
        data["owner"] = owner_username
    
    await create_project_member({
        "user_id": user_details["id"],
        "project_id": project_id,
        "role": owner_role,
        "username": owner_username,
        "designation": owner_designation,
        "is_active": True,
        "created_by": user["username"],
    })
    already_added.add(user["id"])

    # If creator differs, add them as a MEMBER
    if owner_identifier != user["id"]:
        # Find creator's designation if provided
        creator_designation = ""
        if project.team_member_designations:
            designation_entry = next(
                (d for d in project.team_member_designations if d.id == user["id"]), 
                None
            )
            if designation_entry:
                creator_designation = designation_entry.designation
        
        await create_project_member({
            "user_id": user["id"],
            "project_id": project_id,
            "role": RoleEnum.MEMBER.value,
            "username": user["username"],
            "designation": creator_designation,
            "is_active": True,
            "created_by": user["username"],
        })
        already_added.add(owner_identifier)

    # Add selected additional members (if any) as MEMBER
    if project.team_members:
        # member_role_id = None
        # member_role_res = await get_role_by_name(RoleEnum.MEMBER.value)
        # if member_role_res.data:
        #     member_role_id = member_role_res.data[0]["role_id"]
        project_usernames: list[str] = []
        for member_id in project.team_members:
            if member_id in already_added:
                continue
            member_details = await get_user_details_by_id(member_id)
            if not member_details:
                continue
            # Find designation if provided
            member_designation = ""
            if project.team_member_designations:
                designation_entry = next(
                    (d for d in project.team_member_designations if d.id == member_id), 
                    None
                )
                if designation_entry:
                    member_designation = designation_entry.designation
            
            await create_project_member({
                "user_id":  member_details["id"],
                "project_id": project_id,
                "role": RoleEnum.MEMBER.value,
                "username":  member_details["username"],
                "designation": member_designation,
                "is_active": True,
                "created_by":  user["username"],
            })
            project_usernames.append(member_details["username"])
            already_added.add(member_id)
        # Store usernames in projects.team_members for readability
        if project_usernames:
            data["team_members"] = project_usernames

    # Fetch and return the freshly-created ProjectCard
    card = await get_project_card(project_id)
    if card is None:
        raise HTTPException(status_code=500, detail="Unable to fetch created project card")

    # Inject members list for UI (owner + any additional members including creator if distinct)
    card.team_members = list(already_added)
    return card

@router.get("/{org_id}", response_model=List[ProjectCard])
async def list_user_projects(org_id: str, show_all: bool = False, user=Depends(verify_token), org_role=Depends(org_rbac)):
    """
    List projects for the organization.
    
    Parameters:
    - show_all: If true, returns all projects in the organization.
                If false (default), returns only projects where the current user is a member.
    """
    if not org_role:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if show_all:
        return await get_all_org_projects(org_id)
    else:
        return await get_projects_for_user(user["id"], org_id)

@router.get("/detail/{project_id}", response_model=ProjectInDB)
async def read_project(project_id: str, user=Depends(verify_token), proj_role=Depends(project_rbac)):
    if not proj_role:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await get_project(project_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")
    return result.data

@router.put("/{project_id}", response_model=ProjectInDB)
async def update_project_route(project_id: str, project: ProjectUpdate, user=Depends(verify_token), proj_role=Depends(project_rbac)):
    if proj_role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Extract the data to update and remove API-only fields
    project_data = project.dict(exclude_unset=True)
    owner_designation = project_data.pop("owner_designation", None)
    team_member_designations = project_data.pop("team_member_designations", None)
    
    # Update project
    result = await update_project(project_id, {**project_data, "updated_by": user["id"]})
    
    supabase = get_supabase_client()
    
    # If owner designation is provided and there's an owner, update the owner's designation
    if owner_designation is not None and project.owner:
        # Get project member record for owner
        member_query = supabase.from_("project_members").select("*").eq("project_id", project_id).eq("role", "owner").execute()
        
        if member_query.data:
            owner_record = member_query.data[0]
            # Update designation
            supabase.from_("project_members").update({"designation": owner_designation}).eq("id", owner_record["id"]).execute()
    
    # If team member designations provided, update them
    if team_member_designations:
        for member_designation in team_member_designations:
            # Get project member record
            member_query = supabase.from_("project_members").select("*").eq("project_id", project_id).eq("user_id", member_designation.id).execute()
            
            if member_query.data:
                member_record = member_query.data[0]
                # Update designation
                supabase.from_("project_members").update({"designation": member_designation.designation}).eq("id", member_record["id"]).execute()
    
    return result.data[0]

@router.delete("/{project_id}")
async def delete_project_route(project_id: str, user=Depends(verify_token), proj_role=Depends(project_rbac)):
    if proj_role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can delete project")
    await delete_project(project_id)
    return {"ok": True}