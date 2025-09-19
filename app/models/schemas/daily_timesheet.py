from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from uuid import UUID

class DailyTimesheetBase(BaseModel):
    org_id: str = Field(..., description="Organization ID", example="org-1234")
    project_id: str = Field(..., description="Project ID", example="P00001")
    user_id: str = Field(..., description="User ID (UUID)", example="a1b2c3d4-5678-1234-9abc-def012345678")
    entry_date: date = Field(..., description="Date of the timesheet entry", example="2024-12-20")
    in_progress: Optional[str] = Field(None, description="In progress tasks and notes", example="• Working on user authentication\n• Code review for dashboard")
    completed: Optional[str] = Field(None, description="Completed tasks and notes", example="• Fixed login bug\n• Updated documentation")
    blocked: Optional[str] = Field(None, description="Blocked tasks and reasons", example="• API integration - waiting for backend\n• Testing - need QA approval")

class DailyTimesheetCreate(DailyTimesheetBase):
    """Schema for creating a new daily timesheet entry"""
    pass

class DailyTimesheetUpdate(BaseModel):
    """Schema for updating an existing daily timesheet entry"""
    in_progress: Optional[str] = Field(None, description="In progress tasks and notes")
    completed: Optional[str] = Field(None, description="Completed tasks and notes")
    blocked: Optional[str] = Field(None, description="Blocked tasks and reasons")

class DailyTimesheetInDB(DailyTimesheetBase):
    """Schema for daily timesheet as stored in database"""
    id: int = Field(..., description="Primary key")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

class DailyTimesheetWithDetails(DailyTimesheetInDB):
    """Schema for daily timesheet with additional user/project details"""
    user_name: Optional[str] = Field(None, description="User display name")
    user_email: Optional[str] = Field(None, description="User email")
    user_designation: Optional[str] = Field(None, description="User designation")
    project_name: Optional[str] = Field(None, description="Project name")

class DailyTimesheetFilters(BaseModel):
    """Schema for filtering daily timesheets"""
    org_id: str = Field(..., description="Organization ID")
    project_ids: Optional[List[str]] = Field(None, description="Filter by project IDs")
    user_ids: Optional[List[str]] = Field(None, description="Filter by user IDs")
    date_from: Optional[date] = Field(None, description="Start date filter")
    date_to: Optional[date] = Field(None, description="End date filter")

class DailyTimesheetBulkUpdate(BaseModel):
    """Schema for bulk updating multiple timesheet entries"""
    entries: List[DailyTimesheetCreate] = Field(..., description="List of timesheet entries to create/update")

class DailyTimesheetResponse(BaseModel):
    """Schema for API responses containing timesheet data"""
    success: bool = Field(True, description="Whether the operation was successful")
    message: str = Field("Operation completed successfully", description="Response message")
    data: Optional[DailyTimesheetInDB] = Field(None, description="Timesheet data")

class DailyTimesheetListResponse(BaseModel):
    """Schema for API responses containing multiple timesheet entries"""
    success: bool = Field(True, description="Whether the operation was successful")
    message: str = Field("Timesheets retrieved successfully", description="Response message")
    data: List[DailyTimesheetWithDetails] = Field(default_factory=list, description="List of timesheet entries")
    total: int = Field(0, description="Total number of entries")
