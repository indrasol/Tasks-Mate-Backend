from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from app.models.enums import TaskStatusEnum, PriorityEnum

class TrackerBase(BaseModel):
    org_id: str = Field(..., description="Organization ID (text)", example="org-1234")
    project_id: str = Field(..., description="Project ID (text)", example="P00001")
    name: str = Field(..., description="Tracker name", example="Sprint 12 Testing")
    description: Optional[str] = Field(None, description="Tracker description", example="Regression testing for Sprint 12")
    project_name: Optional[str] = Field(None, description="Project name", example="TasksMate Web")
    status: Optional[TaskStatusEnum] = Field(TaskStatusEnum.NOT_STARTED, description="Tracker status", example=TaskStatusEnum.NOT_STARTED)
    priority: Optional[PriorityEnum] = Field(PriorityEnum.LOW, description="Tracker priority", example=PriorityEnum.MEDIUM)
    tags: Optional[List[str]] = Field([], description="List of tags", example=["regression", "sprint-12"])
    metadata: Optional[dict] = Field({}, description="Additional metadata", example={"browser": "Chrome"})
    is_active: Optional[bool] = Field(True, description="Is the tracker active?", example=True)

class TrackerCreate(TrackerBase):
    # Creator fields are optional in the request as they'll be populated from the authenticated user
    creator_id: Optional[UUID] = Field(None, description="Creator user ID (UUID)", example="a1b2c3d4-5678-1234-9abc-def012345678")
    creator_name: Optional[str] = Field(None, description="Creator name", example="John Doe")

class TrackerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    status: Optional[TaskStatusEnum] = None
    priority: Optional[PriorityEnum] = None
    creator_id: Optional[str] = None
    creator_name: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None
    is_active: Optional[bool] = None
    
    class Config:
        orm_mode = True

class TrackerInDB(TrackerBase):
    tracker_id: str
    creator_id: UUID = Field(..., description="Creator user ID (UUID)", example="a1b2c3d4-5678-1234-9abc-def012345678")
    creator_name: str = Field(..., description="Creator name", example="John Doe")
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    delete_reason: Optional[str] = None
    
    class Config:
        orm_mode = True

class TrackerCardView(BaseModel):
    """Simplified tracker representation for list view."""
    tracker_id: str = Field(..., description="Tracker ID", example="TR-0001")
    org_id: str = Field(..., description="Organization ID", example="org-1234")
    project_id: str = Field(..., description="Project ID", example="P00001")
    name: str = Field(..., description="Tracker name", example="Sprint 12 Testing")
    project_name: str = Field(..., description="Project name", example="TasksMate Web")
    creator_id: UUID = Field(..., description="Creator user ID", example="a1b2c3d4-5678-1234-9abc-def012345678")
    creator_name: str = Field(..., description="Creator name", example="John Doe")
    status: TaskStatusEnum = Field(..., description="Status", example=TaskStatusEnum.IN_PROGRESS)
    priority: PriorityEnum = Field(..., description="Priority", example=PriorityEnum.MEDIUM)
    total_bugs: int = Field(0, description="Total number of bugs in the tracker", example=5)
    total_tasks: int = Field(0, description="Total number of tasks in the tracker", example=10)
    created_at: datetime = Field(..., description="Created date", example="2023-01-01T00:00:00Z")
