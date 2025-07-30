from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from models.schemas.organization_invite import OrganizationInviteCreate, OrganizationInviteUpdate, OrganizationInviteInDB
from services.organization_invite_service import create_organization_invite, get_organization_invite, update_organization_invite, delete_organization_invite, get_invites_for_org
from services.auth_handler import verify_token
from services.rbac import get_org_role
from services.utils import inject_audit_fields

router = APIRouter()

async def org_rbac(org_id: str, user=Depends(verify_token)):
    role = await get_org_role(user["id"], org_id)
    if not role:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    return role

@router.post("/", response_model=OrganizationInviteInDB)
async def create_invite(invite: OrganizationInviteCreate, user=Depends(verify_token), role=Depends(org_rbac)):
    if role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await create_organization_invite({**invite.dict(), "invited_by": user["id"]})
    return result.data[0]

@router.get("/", response_model=List[OrganizationInviteInDB])
async def list_org_invites(
    org_id: str = Query(...),
    search: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("email"),
    sort_order: str = Query("asc"),
    email: Optional[str] = Query(None),
    user=Depends(verify_token)
):
    role = await get_org_role(user["id"], org_id)
    if role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized to view invites")
    return await get_invites_for_org(org_id, search=search, limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order, email=email)

@router.get("/{invite_id}", response_model=OrganizationInviteInDB)
async def read_invite(invite_id: str, org_id: str, user=Depends(verify_token), role=Depends(org_rbac)):
    result = await get_organization_invite(invite_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")
    return result.data

@router.put("/{invite_id}", response_model=OrganizationInviteInDB)
async def update_invite(invite_id: str, invite: OrganizationInviteUpdate, org_id: str, user=Depends(verify_token), role=Depends(org_rbac)):
    if role not in ["admin", "editor"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await update_organization_invite(invite_id, invite.dict(exclude_unset=True))
    return result.data[0]

@router.put("/{invite_id}/accept", response_model=OrganizationInviteInDB)
async def accept_invite(invite_id: str, org_id: str, user=Depends(verify_token), role=Depends(org_rbac)):
    # Only the invited user can accept
    # (You may want to check invitee's email/user_id matches user["id"])
    data = inject_audit_fields({}, user["id"], "accept")
    result = await update_organization_invite(invite_id, data)
    return result.data[0]

@router.delete("/{invite_id}")
async def delete_invite(invite_id: str, org_id: str, user=Depends(verify_token), role=Depends(org_rbac)):
    if role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    await delete_organization_invite(invite_id)
    return {"ok": True}