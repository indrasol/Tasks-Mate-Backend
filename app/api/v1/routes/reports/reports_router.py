from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime
from app.services.auth_handler import verify_token
from app.api.v1.routes.organizations.org_rbac import org_rbac
from app.services.reports_service import get_org_reports

router = APIRouter()

class ReportsFilters(BaseModel):
	org_id: str = Field(..., description="Organization ID")
	project_ids: Optional[List[str]] = Field(None, description="Filter by project IDs")
	member_ids: Optional[List[str]] = Field(None, description="Filter by org or project member IDs (user_id)")
	date_from: Optional[datetime] = Field(None, description="Created from (inclusive)")
	date_to: Optional[datetime] = Field(None, description="Created to (inclusive)")
	task_statuses: Optional[List[str]] = Field(None, description="Task statuses to include")
	task_priorities: Optional[List[str]] = Field(None, description="Task priorities to include")
	bug_statuses: Optional[List[str]] = Field(None, description="Bug statuses to include")
	bug_priorities: Optional[List[str]] = Field(None, description="Bug priorities to include")

class ReportsRequest(BaseModel):
	filters: ReportsFilters

@router.post("/org", summary="Org-level reports", description="Side-by-side Projects -> Members -> Tasks/Bugs by Status & Priority. If a filter list is empty or missing, it is treated as 'All'.")
async def org_reports(payload: ReportsRequest, user=Depends(verify_token), role=Depends(org_rbac)) -> Dict[str, Any]:
	# org_rbac ensures access using org_id resolved from query/path/body. Here it’s present in payload.
	try:
		result = await get_org_reports(payload.filters.model_dump())
		return result
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to build reports: {str(e)}")