from typing import List, Optional, Literal
from datetime import date, datetime
from pydantic import BaseModel, Field, constr, conint


GoalStatus = Literal['draft', 'active', 'paused', 'done']


class GoalAssignment(BaseModel):
    userId: str = Field(..., description="Assigned user's ID")
    role: Literal['owner', 'contributor', 'viewer']


class GoalUpdateCreate(BaseModel):
    progress: conint(ge=0, le=100)
    note: Optional[str] = None


class GoalUpdateOut(BaseModel):
    id: str
    goalId: str
    userId: str
    progress: int
    note: Optional[str] = None
    createdAt: datetime


class GoalBase(BaseModel):
    title: constr(min_length=1, max_length=200)
    description: Optional[str] = None
    status: GoalStatus = 'active'
    startDate: Optional[date] = None
    dueDate: Optional[date] = None
    visibility: Optional[Literal['org', 'private']] = 'org'
    assignees: Optional[List[GoalAssignment]] = None


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    title: Optional[constr(min_length=1, max_length=200)] = None
    description: Optional[str] = None
    status: Optional[GoalStatus] = None
    startDate: Optional[date] = None
    dueDate: Optional[date] = None
    visibility: Optional[Literal['org', 'private']] = None
    assignees: Optional[List[GoalAssignment]] = None


class GoalOut(BaseModel):
    id: str
    orgId: str
    title: str
    description: Optional[str] = None
    status: GoalStatus
    startDate: Optional[date] = None
    dueDate: Optional[date] = None
    visibility: Optional[Literal['org', 'private']] = 'org'
    progress: Optional[int] = 0
    assignees: List[GoalAssignment] = []
    createdBy: str
    createdAt: datetime
    updatedAt: datetime


class GoalListFilters(BaseModel):
    userId: Optional[str] = None
    status: Optional[Literal['draft', 'active', 'paused', 'done', 'all']] = None
    q: Optional[str] = None
    page: int = 1
    pageSize: int = 20
    dueStart: Optional[date] = None
    dueEnd: Optional[date] = None


class PaginatedGoals(BaseModel):
    items: List[GoalOut]
    total: int
    page: int
    pageSize: int



