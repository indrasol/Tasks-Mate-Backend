from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import uuid

class TimesheetEntry(BaseModel):
    """Individual timesheet entry model"""
    id: str = Field(..., description="Unique entry ID")
    title: str = Field(..., description="Entry title/description", min_length=1, max_length=500)
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    blocked_since: Optional[str] = Field(None, description="When it was blocked")

    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

class UserTimesheetData(BaseModel):
    """Complete timesheet data structure"""
    in_progress: List[TimesheetEntry] = Field(default_factory=list, description="In progress tasks")
    completed: List[TimesheetEntry] = Field(default_factory=list, description="Completed tasks")
    blocked: List[TimesheetEntry] = Field(default_factory=list, description="Blocked tasks")

class UserTimesheetCreate(BaseModel):
    """Schema for creating/updating timesheet fields"""
    org_id: str = Field(..., description="Organization ID", min_length=1)
    user_id: str = Field(..., description="User ID", min_length=1)
    entry_date: date = Field(..., description="Entry date")
    field_type: str = Field(..., description="Field type: 'in_progress', 'completed', or 'blocked'")
    field_content: str = Field(..., description="Text content for the field", max_length=5000)

    @validator('field_type')
    def validate_field_type(cls, v):
        allowed_types = ['in_progress', 'completed', 'blocked']
        if v not in allowed_types:
            raise ValueError(f'field_type must be one of: {allowed_types}')
        return v

    @validator('entry_date')
    def validate_entry_date(cls, v):
        # Don't allow future dates beyond reasonable limit (e.g., 1 day)
        from datetime import date, timedelta
        max_future_date = date.today() + timedelta(days=1)
        if v > max_future_date:
            raise ValueError('Entry date cannot be more than 1 day in the future')
        return v

class UserTimesheetInDB(BaseModel):
    """Schema for timesheet as stored in database"""
    id: int = Field(..., description="Primary key")
    org_id: str = Field(..., description="Organization ID")
    user_id: str = Field(..., description="User ID")
    entry_date: str = Field(..., description="Entry date")
    timesheet_data: Dict[str, Any] = Field(..., description="JSONB timesheet data")
    has_data: bool = Field(..., description="Whether timesheet has any data")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

class TeamTimesheetUser(BaseModel):
    """Team member with timesheet data"""
    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="Display name")
    email: str = Field(..., description="Email address")
    designation: str = Field(default="Team Member", description="Job designation")
    avatar_initials: str = Field(..., description="Avatar initials")
    role: str = Field(default="member", description="Organization role")
    in_progress: List[TimesheetEntry] = Field(default_factory=list)
    completed: List[TimesheetEntry] = Field(default_factory=list)
    blocked: List[TimesheetEntry] = Field(default_factory=list)

class UserTimesheetResponse(BaseModel):
    """Standard API response for timesheet operations"""
    success: bool = Field(default=True, description="Operation success status")
    message: str = Field(default="Success", description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")

class TeamTimesheetsResponse(BaseModel):
    """Response for team timesheet queries"""
    success: bool = Field(default=True)
    message: str = Field(default="Success")
    users: List[TeamTimesheetUser] = Field(default_factory=list)
    date: str = Field(..., description="Query date")
    org_id: str = Field(..., description="Organization ID")

class CalendarStatusEntry(BaseModel):
    """Calendar status for a single date"""
    hasData: bool = Field(default=False, description="Whether date has timesheet data")
    userCount: int = Field(default=0, description="Number of users with data")

class CalendarStatusResponse(BaseModel):
    """Response for calendar month status"""
    success: bool = Field(default=True)
    message: str = Field(default="Success")
    calendar_status: Dict[str, CalendarStatusEntry] = Field(default_factory=dict)
    year: int = Field(..., description="Year")
    month: int = Field(..., description="Month")
    org_id: str = Field(..., description="Organization ID")
