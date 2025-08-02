from fastapi import Request, Depends, HTTPException
from typing import Optional
from app.services.auth_handler import verify_token
from app.services.rbac import get_project_role

async def project_rbac(request: Request, user=Depends(verify_token)) -> str:
    project_id: Optional[str] = None

    # 1. Query parameters
    project_id = request.query_params.get("project_id")

    # 2. Path parameters
    if not project_id:
        project_id = request.path_params.get("project_id")

    # 3. Body (only for methods that support a body)
    if not project_id and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        try:
            body = await request.json()
            project_id = body.get("project_id")
        except Exception:
            pass  # Ignore malformed or missing JSON

    if not project_id:
        raise HTTPException(status_code=400, detail="project_id is required for RBAC")

    # 4. Check user's role in the org
    role = await get_project_role(user["id"], project_id)
    if not role:
        raise HTTPException(status_code=403, detail="Access denied")
    # else:
    #     raise HTTPException(status_code=403, detail=str(role))

    return role
