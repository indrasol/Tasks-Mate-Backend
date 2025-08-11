from datetime import datetime 
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from app.api.v1.routes.organizations.org_rbac import org_rbac
from app.models.schemas.organization_invite import OrganizationInviteCreate, OrganizationInviteUpdate, OrganizationInviteInDB
from app.services.organization_invite_service import create_organization_invite, get_organization_invite, update_organization_invite, delete_organization_invite, get_invites_for_org, get_invites_for_user
from app.services.auth_handler import verify_token
from app.services.organization_member_service import create_organization_member
from app.services.rbac import get_org_role
from app.services.utils import inject_audit_fields

router = APIRouter()

# async def org_rbac(org_id: str, user=Depends(verify_token)):
#     role = await get_org_role(user["id"], org_id)
#     if not role:
#         raise HTTPException(status_code=403, detail="Not a member of this organization")
#     return role

# from fastapi import Request, Depends, HTTPException
# from typing import Optional

# async def org_rbac(request: Request, user=Depends(verify_token)) -> str:
#     org_id: Optional[str] = None

#     # 1. Query parameters
#     org_id = request.query_params.get("org_id")

#     # 2. Path parameters
#     if not org_id:
#         org_id = request.path_params.get("org_id")

#     # 3. Body (only for methods that support a body)
#     if not org_id and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
#         try:
#             body = await request.json()
#             org_id = body.get("org_id")
#         except Exception:
#             pass  # Ignore malformed or missing JSON

#     if not org_id:
#         raise HTTPException(status_code=400, detail="org_id is required for RBAC")

#     # 4. Check user's role in the org
#     role = await get_org_role(user["id"], org_id)
#     if not role:
#         raise HTTPException(status_code=403, detail="Access denied")
#     # else:
#     #     raise HTTPException(status_code=403, detail=str(role))

#     return role



@router.post("", response_model=OrganizationInviteInDB)
async def create_invite(invite: OrganizationInviteCreate, user=Depends(verify_token), role=Depends(org_rbac)):
    if role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    data = inject_audit_fields(invite.dict(), user["username"], action="invite_org")

    result = await create_organization_invite(data)
    return result.data[0]

@router.get("/org/{org_id}", response_model=List[OrganizationInviteInDB])
async def list_org_invites(
    org_id: str,
    search: Optional[str] = Query(None),
    limit: Optional[int] = Query(20, ge=1, le=100),
    offset: Optional[int] = Query(0, ge=0),
    sort_by: Optional[str] = Query("email"),
    sort_order: Optional[str] = Query("asc"),
    email: Optional[str] = Query(None),
    user=Depends(verify_token)
):
    role = await get_org_role(user["id"], org_id)
    if role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized to view invites")
    return await get_invites_for_org(org_id, search=search, limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order, email=email)


@router.get("/user", response_model=List[OrganizationInviteInDB])
async def list_user_invites(
    user=Depends(verify_token)
):
    return await get_invites_for_user(user["email"])


@router.get("/org/{invite_id}", response_model=OrganizationInviteInDB)
async def read_invite(invite_id: str, user=Depends(verify_token), role=Depends(org_rbac)):
    result = await get_organization_invite(invite_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")
    return result.data

@router.put("/{invite_id}", response_model=OrganizationInviteInDB)
async def update_invite(invite_id: str, invite: OrganizationInviteUpdate, user=Depends(verify_token), role=Depends(org_rbac)):
    if role not in ["admin", "editor"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await update_organization_invite(invite_id, invite.dict(exclude_unset=True))
    return result.data[0]

@router.put("/{invite_id}/accept", response_model=OrganizationInviteInDB)
async def accept_invite(invite_id: str, user=Depends(verify_token)):
    # Only the invited user can accept
    # (You may want to check invitee's email/user_id matches user["id"])
    # Check if invite exists
    invite = await get_organization_invite(invite_id)
    if not invite.data:
        raise HTTPException(status_code=404, detail="Not found")
    if invite.data["email"] != user["email"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    # Check if invite is already accepted
    # if invite.data["invite_status"] == "accepted":
    #     raise HTTPException(status_code=400, detail="Invite already accepted")
    # Check if invite is already expired
    # expires_at = datetime.fromisoformat(invite.data["expires_at"])
    # if expires_at < datetime.utcnow():
    #     raise HTTPException(status_code=400, detail="Invite expired")
    # if invite.data["expires_at"] < datetime.now():
    #     
    # Update invite status to accepted
    invite.data["invite_status"] = "accepted"
    invite.data["updated_at"] = datetime.utcnow().isoformat()
    # Update invite
    result = await update_organization_invite(invite_id, invite.data)
    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to update invite")
        
    # Create organization member
    result_member = await create_organization_member({
        "user_id": user["id"],
        "org_id": invite.data["org_id"],
        "email": user["email"],
        "username":user["username"],
        "role": invite.data["role"],
        "designation": invite.data["designation"],
        "invited_by": invite.data["invited_by"],
        "invited_at": invite.data.get("invited_at"),
        "accepted_at": datetime.utcnow().isoformat()
    })

    result_invite = await delete_organization_invite(invite_id)
    
    return result.data[0]

@router.delete("/{invite_id}")
async def delete_invite(invite_id: str, user=Depends(verify_token), role=Depends(org_rbac)):
    if role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    await delete_organization_invite(invite_id)
    return {"ok": True}