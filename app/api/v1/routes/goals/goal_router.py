from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse
import logging

from app.services.auth_handler import verify_token
from app.api.v1.routes.organizations.org_rbac import org_rbac
from app.models.schemas.goal import (
    GoalCreate, GoalUpdate, GoalOut, GoalListFilters, PaginatedGoals, GoalUpdateCreate
)
from app.services.goal_service import GoalService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=PaginatedGoals)
async def list_goals(
    org_id: str = Query(...),
    userId: Optional[str] = Query(None),
    status_q: Optional[str] = Query(None, alias="status"),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100, alias="pageSize"),
    dueStart: Optional[str] = Query(None),
    dueEnd: Optional[str] = Query(None),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    try:
        if org_role not in ['member', 'admin', 'owner']:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        due_start = None
        due_end = None
        from datetime import date
        if dueStart:
            due_start = date.fromisoformat(dueStart)
        if dueEnd:
            due_end = date.fromisoformat(dueEnd)

        data = await GoalService.list_goals(org_id, userId, status_q, q, page, pageSize, due_start, due_end)
        return PaginatedGoals(**data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing goals: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=GoalOut)
async def create_goal(
    payload: GoalCreate,
    org_id: str = Query(...),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    try:
        current_user_id = user.get("id")
        if org_role not in ['member', 'admin', 'owner']:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        goal = await GoalService.create_goal(org_id, current_user_id, payload.model_dump(mode='json'))
        # Map to GoalOut
        out = GoalOut(
            id=str(goal.get('id')),
            orgId=str(goal.get('org_id')),
            title=goal.get('title'),
            description=goal.get('description'),
            status=goal.get('status'),
            startDate=goal.get('start_date'),
            dueDate=goal.get('due_date'),
            visibility=goal.get('visibility') or 'org',
            progress=0,
            assignees=payload.assignees or [],
            category=goal.get('category') or [],
            subCategory=goal.get('sub_category') or [],
            sectionId=goal.get('section_id'),
            createdBy=str(goal.get('created_by')),
            createdAt=goal.get('created_at'),
            updatedAt=goal.get('updated_at'),
        )
        return out
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating goal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{goal_id}", response_model=GoalOut)
async def get_goal(
    goal_id: str = Path(...),
    org_id: str = Query(...),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    try:
        if org_role not in ['member', 'admin', 'owner']:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        data = await GoalService.list_goals(org_id)
        match = next((g for g in data['items'] if str(g['id']) == str(goal_id)), None)
        if not match:
            raise HTTPException(status_code=404, detail="Goal not found")
        return GoalOut(**match)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting goal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{goal_id}", response_model=GoalOut)
async def update_goal(
    goal_id: str,
    payload: GoalUpdate,
    org_id: str = Query(...),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    try:
        if org_role not in ['admin', 'owner']:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        updated = await GoalService.update_goal(org_id, goal_id, payload.model_dump(exclude_none=True, mode='json'))
        # Re-read single goal mapped
        data = await GoalService.list_goals(org_id)
        match = next((g for g in data['items'] if str(g['id']) == str(goal_id)), None)
        if not match:
            raise HTTPException(status_code=404, detail="Goal not found")
        return GoalOut(**match)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating goal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: str,
    org_id: str = Query(...),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    try:
        if org_role not in ['admin', 'owner']:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        await GoalService.delete_goal(org_id, goal_id)
        return {"success": True, "message": "Goal deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting goal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{goal_id}/updates")
async def add_goal_update(
    goal_id: str,
    payload: GoalUpdateCreate,
    org_id: str = Query(...),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    try:
        current_user_id = user.get("id")
        if org_role not in ['member', 'admin', 'owner']:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        upd = await GoalService.add_update(org_id, goal_id, current_user_id, payload.progress, payload.note)
        return {"success": True, "data": upd}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding goal update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{goal_id}/updates")
async def list_goal_updates(
    goal_id: str,
    org_id: str = Query(...),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    try:
        if org_role not in ['member', 'admin', 'owner']:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        rows = await GoalService.list_updates(org_id, goal_id)
        return {"success": True, "data": rows}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing goal updates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("-sections")
async def list_sections(
    org_id: str = Query(...),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    try:
        if org_role not in ['member', 'admin', 'owner']:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        rows = await GoalService.list_sections(org_id)
        return rows
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing goal sections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("-sections")
async def create_section(
    body: dict,
    org_id: str = Query(...),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    try:
        if org_role not in ['admin', 'owner']:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        title = (body or {}).get('title') or ''
        order = int((body or {}).get('order') or 0)
        row = await GoalService.create_section(org_id, title, order)
        return row
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating goal section: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("-sections/{section_id}")
async def update_section(
    section_id: str = Path(...),
    body: dict = {},
    org_id: str = Query(...),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    try:
        if org_role not in ['admin', 'owner']:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        row = await GoalService.update_section(org_id, section_id, body or {})
        return row
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating goal section: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("-sections/{section_id}")
async def delete_section(
    section_id: str = Path(...),
    org_id: str = Query(...),
    user=Depends(verify_token),
    org_role=Depends(org_rbac)
):
    try:
        if org_role not in ['admin', 'owner']:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        await GoalService.delete_section(org_id, section_id)
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting goal section: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


