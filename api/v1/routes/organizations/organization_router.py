from fastapi import APIRouter, Depends, HTTPException
from models.schemas.organization import OrganizationCreate, OrganizationUpdate, OrganizationInDB
from services.organization_service import create_organization, get_organization, update_organization, delete_organization
from services.auth_handler import verify_token
from services.rbac import get_org_role
from services.organization_member_service import create_organization_member

router = APIRouter()

async def org_rbac(org_id: str, user=Depends(verify_token)):
    role = await get_org_role(user["id"], org_id)
    if not role:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    return role

@router.post("/", response_model=OrganizationInDB)
async def create_org(org: OrganizationCreate, user=Depends(verify_token)):
    # Only global admin/editor can create orgs
    if user.get("role") not in ["admin", "editor"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await create_organization({**org.dict(), "created_by": user["id"]})
    org_id = result.data[0]["org_id"]
    await create_organization_member({
        "user_id": user["id"],
        "org_id": org_id,
        "role": "owner",
        "is_active": True,
        "created_by": user["id"]
    })
    return result.data[0]

@router.get("/{org_id}", response_model=OrganizationInDB)
async def read_org(org_id: str, user=Depends(verify_token), role=Depends(org_rbac)):
    result = await get_organization(org_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")
    return result.data

@router.put("/{org_id}", response_model=OrganizationInDB)
async def update_org(org_id: str, org: OrganizationUpdate, user=Depends(verify_token), role=Depends(org_rbac)):
    if role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await update_organization(org_id, {**org.dict(exclude_unset=True), "updated_by": user["id"]})
    return result.data[0]

@router.delete("/{org_id}")
async def delete_org(org_id: str, user=Depends(verify_token), role=Depends(org_rbac)):
    if role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can delete organization")
    await delete_organization(org_id, {"deleted_by": user["id"]})
    return {"ok": True}