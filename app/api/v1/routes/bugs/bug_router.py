from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, UploadFile, File

from app.services.auth_handler import verify_token

from app.models.schemas.bug import (
    BugCreate, BugUpdate, BugInDB, BugWithRelations,
    BugCommentCreate, BugCommentInDB, BugCommentWithUser,
    BugAttachmentInDB, BugRelationCreate, BugRelationInDB,
    BugStatusEnum, BugPriorityEnum, BugTypeEnum
)
from app.services.bug_service import (
    create_bug, get_bug, update_bug, delete_bug,
    create_bug_comment, get_bug_comments,
    create_bug_attachment, create_bug_relation,
    search_bugs
)

# Import sub-routers 
from .comment_router import router as comment_router
from .attachment_router import router as attachment_router
from .history_router import router as history_router
from .watcher_router import router as watcher_router

router = APIRouter()

# Include sub-routers
router.include_router(comment_router, prefix="/{bug_id}", tags=["bug_comments"])
router.include_router(attachment_router, prefix="/{bug_id}", tags=["bug_attachments"])
router.include_router(history_router, prefix="/{bug_id}", tags=["bug_history"])
router.include_router(watcher_router, prefix="/{bug_id}", tags=["bug_watchers"])

@router.post("", response_model=BugInDB, status_code=status.HTTP_201_CREATED)
async def create_new_bug(
    bug: BugCreate,
    current_user: dict = Depends(verify_token)    
):
    """Create a new bug."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        # Set the reporter to the current user's username
        bug_dict = bug.dict(exclude_unset=True)
        bug_dict["reporter"] = current_user["username"]
        
        result = await create_bug(BugCreate(**bug_dict), current_user["username"])
        if not result or not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create bug"
            )
        return result.data[0] if isinstance(result.data, list) else result.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# @router.get("/search/{tracker_id}", response_model=list[BugInDB])
# async def list_bugs_endpoint(
#     tracker_id: str,
#     current_user: dict = Depends(verify_token)
# ):
#     """List all bugs."""
#     if not current_user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Not authenticated"
#         )
    
#     try:
#         result = await list_bugs(tracker_id)
#         return result.data if result.data else []
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )

@router.get("/search/{tracker_id}", response_model=dict)
async def search_bugs_endpoint(
    tracker_id: str,
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    status: Optional[List[BugStatusEnum]] = Query(None, description="Filter by status"),
    priority: Optional[List[BugPriorityEnum]] = Query(None, description="Filter by priority"),
    type: Optional[List[BugTypeEnum]] = Query(None, description="Filter by type"),
    assignee: Optional[List[str]] = Query(None, description="Filter by assignee username"),
    reporter: Optional[List[str]] = Query(None, description="Filter by reporter username"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    sort_by: str = Query("updated_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(verify_token)
):
    """Search and filter bugs with pagination."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        result = await search_bugs(
            tracker_id=tracker_id,
            project_id=project_id,
            status=status,
            priority=priority,
            type=type,
            assignee=assignee,
            reporter=reporter,
            tags=tags,
            search_query=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{bug_id}", response_model=BugWithRelations)
async def get_bug_by_id(
    bug_id: str = Path(..., description="The ID of the bug to retrieve"),
    current_user: dict = Depends(verify_token)    
):
    """Get a bug by ID with all related data."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        bug = await get_bug(bug_id)
        if not bug:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bug not found"
            )
        return bug
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{bug_id}", response_model=BugInDB)
async def update_bug_by_id(
    bug_id: str,
    bug_update: BugUpdate,
    current_user: dict = Depends(verify_token)    
):
    """Update a bug by ID."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        result = await update_bug(bug_id, bug_update, current_user["username"])
        if not result or not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bug not found or update failed"
            )
        return result.data[0] if isinstance(result.data, list) else result.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{bug_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bug_by_id(
    bug_id: str,
    current_user: dict = Depends(verify_token)    
):
    """Delete a bug by ID."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        result = await delete_bug(bug_id, current_user["username"])
        if not result or not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bug not found"
            )
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{bug_id}/comments", response_model=BugCommentInDB, status_code=status.HTTP_201_CREATED)
async def add_comment_to_bug(
    bug_id: str,
    comment: BugCommentCreate,
    current_user: dict = Depends(verify_token)    
):
    """Add a comment to a bug."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        result = await create_bug_comment(bug_id, comment, current_user["username"])
        if not result or not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add comment"
            )
        return result.data[0] if isinstance(result.data, list) else result.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{bug_id}/comments", response_model=List[BugCommentWithUser])
async def get_comments_for_bug(
    bug_id: str,
    current_user: dict = Depends(verify_token)    
):
    """Get all comments for a bug."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        comments = await get_bug_comments(bug_id)
        return comments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{bug_id}/attachments", response_model=BugAttachmentInDB, status_code=status.HTTP_201_CREATED)
async def upload_bug_attachment(
    bug_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(verify_token)    
):
    """Upload an attachment for a bug."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        result = await create_bug_attachment(bug_id, file, current_user["username"])
        if not result or not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload attachment"
            )
        return result.data[0] if isinstance(result.data, list) else result.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{bug_id}/relations", response_model=BugRelationInDB, status_code=status.HTTP_201_CREATED)
async def add_relation_to_bug(
    bug_id: str,
    relation: BugRelationCreate,
    current_user: dict = Depends(verify_token)    
):
    """Add a relation between two bugs."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        result = await create_bug_relation(bug_id, relation, current_user["username"])
        if not result or not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create relation"
            )
        return result.data[0] if isinstance(result.data, list) else result.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
