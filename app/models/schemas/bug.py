from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.enums import BugPriorityEnum, BugStatusEnum, BugTypeEnum

# Base models
class BugBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Title of the bug")
    description: Optional[str] = Field(None, description="Detailed description of the bug")
    status: BugStatusEnum = Field(default=BugStatusEnum.OPEN, description="Current status of the bug")
    priority: BugPriorityEnum = Field(default=BugPriorityEnum.MEDIUM, description="Priority level of the bug")
    type: BugTypeEnum = Field(default=BugTypeEnum.BUG, description="Type of the bug")
    assignee: Optional[str] = Field(None, description="Username of the user assigned to the bug")
    project_id: str = Field(..., description="ID of the project this bug belongs to")
    project_name: Optional[str] = Field(None, description="Name of the project")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing the bug")
    due_date: Optional[datetime] = Field(None, description="Due date for the bug")
    estimated_time: Optional[timedelta] = Field(None, description="Estimated time to fix")
    actual_time: Optional[timedelta] = Field(None, description="Actual time taken to fix")
    environment: Optional[str] = Field(None, description="Environment where the bug occurs")
    steps_to_reproduce: Optional[str] = Field(None, description="Steps to reproduce the bug")
    expected_result: Optional[str] = Field(None, description="Expected result")
    actual_result: Optional[str] = Field(None, description="Actual result")
    tracker_id: Optional[str] = Field(None, description="ID of the test tracker this bug is associated with")
    tracker_name: Optional[str] = Field(None, description="Name of the test tracker")
    closed_at: Optional[datetime] = Field(None, description="Date when the bug was closed")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            timedelta: lambda v: str(v) if v else None
        }

class BugCreate(BugBase):
    reporter: Optional[str] = Field(None, description="Username of the user reporting the bug")

class BugUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Title of the bug")
    description: Optional[str] = Field(None, description="Detailed description of the bug")
    status: Optional[BugStatusEnum] = Field(None, description="Current status of the bug")
    priority: Optional[BugPriorityEnum] = Field(None, description="Priority level of the bug")
    type: Optional[BugTypeEnum] = Field(None, description="Type of the bug")
    assignee: Optional[str] = Field(None, description="Username of the user assigned to the bug")
    project_id: Optional[str] = Field(None, description="ID of the project this bug belongs to")
    project_name: Optional[str] = Field(None, description="Name of the project")
    tags: Optional[List[str]] = Field(None, description="Tags for categorizing the bug")
    due_date: Optional[datetime] = Field(None, description="Due date for the bug")
    estimated_time: Optional[timedelta] = Field(None, description="Estimated time to fix")
    actual_time: Optional[timedelta] = Field(None, description="Actual time taken to fix")
    environment: Optional[str] = Field(None, description="Environment where the bug occurs")
    steps_to_reproduce: Optional[str] = Field(None, description="Steps to reproduce the bug")
    expected_result: Optional[str] = Field(None, description="Expected result")
    actual_result: Optional[str] = Field(None, description="Actual result")
    tracker_id: Optional[str] = Field(None, description="ID of the test tracker this bug is associated with")
    tracker_name: Optional[str] = Field(None, description="Name of the test tracker")
    closed_at: Optional[datetime] = Field(None, description="Date when the bug was closed")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            timedelta: lambda v: str(v) if v else None
        }

class BugInDB(BugBase):
    id: str
    reporter: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# Comment models
class BugCommentBase(BaseModel):
    content: str = Field(..., min_length=1, description="The comment content")

class BugCommentCreate(BugCommentBase):
    pass

class BugCommentUpdate(BugCommentBase):
    content: Optional[str] = Field(None, min_length=1, description="The updated comment content")

class BugCommentInDB(BugCommentBase):
    id: str
    bug_id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# Attachment models
class BugAttachmentBase(BaseModel):
    file_name: str = Field(..., description="Original name of the file")
    file_path: str = Field(..., description="Path to the stored file")
    file_type: Optional[str] = Field(None, description="MIME type of the file")
    file_size: Optional[int] = Field(None, description="Size of the file in bytes")

class BugAttachmentCreate(BugAttachmentBase):
    pass

class BugAttachmentInDB(BugAttachmentBase):
    id: str
    bug_id: str
    user_id: str
    created_at: datetime

    class Config:
        orm_mode = True

# Activity log models
class BugActivityLogInDB(BaseModel):
    id: str
    bug_id: str
    user_id: str
    activity_type: str
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        orm_mode = True

# Watcher models
class BugWatcherInDB(BaseModel):
    bug_id: str
    user_id: str
    created_at: datetime

    class Config:
        orm_mode = True

# Relation models
class BugRelationBase(BaseModel):
    target_bug_id: str = Field(..., description="ID of the related bug")
    relation_type: str = Field(..., description="Type of relation (e.g., 'duplicate', 'blocks', 'related_to')")

class BugRelationCreate(BugRelationBase):
    pass

class BugRelationInDB(BugRelationBase):
    source_bug_id: str
    created_by: str
    created_at: datetime

    class Config:
        orm_mode = True

# Response models with relationships
class BugWithRelations(BugInDB):
    comments: List[BugCommentInDB] = []
    attachments: List[BugAttachmentInDB] = []
    activity_logs: List[BugActivityLogInDB] = []
    watchers: List[BugWatcherInDB] = []
    related_bugs: List[Dict[str, Any]] = []

class BugCommentWithUser(BugCommentInDB):
    user_id: Dict[str, Any] = Field(..., description="User who created the comment")

class BugActivityLogWithUser(BugActivityLogInDB):
    user_id: Dict[str, Any] = Field(..., description="User who performed the action")

# Filter models
class BugFilter(BaseModel):
    status: Optional[List[BugStatusEnum]] = None
    priority: Optional[List[BugPriorityEnum]] = None
    type: Optional[List[BugTypeEnum]] = None
    assignee: Optional[List[str]] = None
    reporter: Optional[List[str]] = None
    project_id: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class BugSearchParams(BaseModel):
    """Standardized parameters for bug search and filtering."""
    project_id: Optional[str] = Field(None, description="Filter by project ID")
    status: Optional[List[BugStatusEnum]] = Field(None, description="Filter by status")
    priority: Optional[List[BugPriorityEnum]] = Field(None, description="Filter by priority")
    type: Optional[List[BugTypeEnum]] = Field(None, description="Filter by type")
    assignee: Optional[List[str]] = Field(None, description="Filter by assignee username")
    reporter: Optional[List[str]] = Field(None, description="Filter by reporter username")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    search_query: Optional[str] = Field(None, description="Search in title and description")
    sort_by: str = Field("updated_at", description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
