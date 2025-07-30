from fastapi import APIRouter, Depends, HTTPException
from models.schemas.organization_invite import OrganizationInviteCreate, OrganizationInviteUpdate, OrganizationInviteInDB
from services.organization_invite_service import create_organization_invite, get_organization_invite, update_organization_invite, delete_organization_invite
from services.auth_handler import verify_token
from services.rbac import get_org_role

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

@router.delete("/{invite_id}")
async def delete_invite(invite_id: str, org_id: str, user=Depends(verify_token), role=Depends(org_rbac)):
    if role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    await delete_organization_invite(invite_id)
    return {"ok": True}