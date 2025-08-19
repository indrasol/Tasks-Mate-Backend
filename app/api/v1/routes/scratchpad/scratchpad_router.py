from fastapi import APIRouter, Depends, HTTPException
from app.services.auth_handler import verify_token
from app.services.scratchpad_service import get_scratchpad, upsert_scratchpad
from app.services.organization_service import get_organization
import datetime
from app.models.schemas.scratchpad import ScratchpadCreate, ScratchpadInDB

router = APIRouter()


@router.get("/{org_id}", response_model=ScratchpadInDB)
async def read_scratchpad(org_id: str, user=Depends(verify_token)):
    res = await get_scratchpad(org_id, user["id"])
    data = getattr(res, "data", None)
    if not data:
        # Return empty scratchpad structure
        return {
            "org_id": org_id,
            "user_id": user["id"],
            "org_name": None,
            "user_name": user["username"],
            "content": "",
            "created_at": None,
            "updated_at": None,
        }
    return data


@router.post("", response_model=ScratchpadInDB)
async def save_scratchpad(payload: ScratchpadCreate, user=Depends(verify_token)):
    # Resolve org_name from org_id
    org_name = ""
    # org_res = await get_organization(payload.org_id)
    # if org_res and org_res.data:
    #     org_name = org_res.data[0].get("name", "")

    data = {
        **payload.model_dump(),
        # "org_name": org_name,
        "user_id": user["id"],
        "user_name": user.get("username"),
        "updated_at": datetime.datetime.utcnow().isoformat(),
    }
    res = await upsert_scratchpad(data)
    return res.get("data", [data])[0] if isinstance(res, dict) else data
