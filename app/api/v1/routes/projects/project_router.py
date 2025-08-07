from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.api.v1.routes.organizations.org_rbac import org_rbac
from app.api.v1.routes.projects.proj_rbac import project_rbac
from app.models.enums import RoleEnum
from app.models.schemas.project import ProjectCard, ProjectCreate, ProjectUpdate, ProjectInDB
from app.services.project_service import create_project, get_project, update_project, delete_project, get_projects_for_user, get_project_card
from app.services.auth_handler import verify_token
from app.services.rbac import get_project_role
from app.services.project_member_service import create_project_member
from app.services.role_service import create_role, get_role_by_name
from app.services.utils import inject_audit_fields
from app.services.user_service import get_user_details_by_username

router = APIRouter()



@router.post("/", response_model=ProjectCard)
async def create_project_route(project: ProjectCreate, user=Depends(verify_token), org_role=Depends(org_rbac)):
    """Create a project and immediately return a fully-hydrated `ProjectCard` instance."""
    # Only organization owner/admin can create projects
    if org_role not in [RoleEnum.OWNER.value, RoleEnum.ADMIN.value]:
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
    owner_name = project.owner or user["id"]

    # Ensure OWNER role exists
    role_res = await get_role_by_name(RoleEnum.OWNER.value)
    if role_res.data:
        owner_role = role_res.data[0]["name"]

    already_added: set[str] = set()

    # Insert owner membership
    await create_project_member({
        "user_id": user["id"],
        "project_id": project_id,
        "role": owner_role,
        "username": user["username"],
        "is_active": True,
        "created_by": user["username"],
    })
    already_added.add(user["id"])

    # If creator differs, add them as ADMIN (or OWNER if admin role absent)
    if owner_name != user["id"]:
        # user_details = await get_user_details_by_username(owner_name)
        await create_project_member({
            # "user_id": user_details["id"],
            "user_id": owner_name,
            "project_id": project_id,
            "role": owner_role,
            "username": owner_name,
            "is_active": True,
            "created_by":  user["username"],
        })
        already_added.add(owner_name)

    # Add selected additional members (if any) as MEMBER
    if project.team_members:
        member_role_id = None
        member_role_res = await get_role_by_name(RoleEnum.MEMBER.value)
        if member_role_res.data:
            member_role_id = member_role_res.data[0]["role_id"]
        for member in project.team_members:
            if member in already_added:
                continue
            # user_details = await get_user_details_by_username(member)
            await create_project_member({
                # "user_id": user_details["id"],
                "user_id": member,
                "project_id": project_id,
                "role": RoleEnum.MEMBER.value,
                "username": member,
                "is_active": True,
                "created_by":  user["username"],
            })
            already_added.add(member)

    # Fetch and return the freshly-created ProjectCard
    card = await get_project_card(project_id)
    if card is None:
        raise HTTPException(status_code=500, detail="Unable to fetch created project card")

    # Inject members list for UI (owner + any additional members including creator if distinct)
    card.team_members = list(already_added)
    return card

@router.get("/{org_id}", response_model=List[ProjectCard])
async def list_user_projects(org_id: str, user=Depends(verify_token), org_role=Depends(org_rbac)):
    """
    List all projects where the current user is a member.
    """
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
    result = await update_project(project_id, {**project.dict(exclude_unset=True), "updated_by": user["id"]})
    return result.data[0]

@router.delete("/{project_id}")
async def delete_project_route(project_id: str, user=Depends(verify_token), proj_role=Depends(project_rbac)):
    if proj_role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can delete project")
    await delete_project(project_id, {"deleted_by": user["id"]})
    return {"ok": True}