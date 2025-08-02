
from fastapi import Request, Depends, HTTPException
from typing import Optional
from app.services.auth_handler import verify_token
from app.services.rbac import get_org_role

async def org_rbac(request: Request, user=Depends(verify_token)) -> str:
    org_id: Optional[str] = None

    # 1. Query parameters
    org_id = request.query_params.get("org_id")

    # 2. Path parameters
    if not org_id:
        org_id = request.path_params.get("org_id")

    # 3. Body (only for methods that support a body)
    if not org_id and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        try:
            body = await request.json()
            org_id = body.get("org_id")
        except Exception:
            pass  # Ignore malformed or missing JSON

    if not org_id:
        raise HTTPException(status_code=400, detail="org_id is required for RBAC")

    # 4. Check user's role in the org
    role = await get_org_role(user["id"], org_id)
    if not role:
        raise HTTPException(status_code=403, detail="Access denied")
    # else:
    #     raise HTTPException(status_code=403, detail=str(role))

    return role
