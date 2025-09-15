from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from decimal import Decimal

class KPIData(BaseModel):
    total_tasks: int = Field(..., description="Total number of tasks")
    active_projects: int = Field(..., description="Number of active projects")
    completed_projects: int = Field(..., description="Number of completed projects")
    blocked_projects: int = Field(..., description="Number of blocked projects")
    team_members: int = Field(..., description="Number of team members")
    tasks_this_month: Optional[int] = Field(None, description="Tasks created this month")
    tasks_prev_month: Optional[int] = Field(None, description="Tasks created in the previous month")
    tasks_mom_pct: Optional[float] = Field(None, description="Month over month percentage change in tasks")
    new_projects_this_month: Optional[int] = Field(None, description="New projects created this month")
    projects_completed_this_month: Optional[int] = Field(None, description="Projects completed this month")

class ProjectStatusItem(BaseModel):
    name: str = Field(..., description="Status name")
    value: int = Field(..., description="Count of projects with this status")
    color: str = Field(..., description="Color code for visualization")

class TaskCompletionTrendItem(BaseModel):
    month: str = Field(..., description="Month name")
    completed: int = Field(..., description="Number of completed tasks")
    pending: int = Field(..., description="Number of pending tasks")
    blocked: int = Field(..., description="Number of blocked tasks")

class TeamProductivityItem(BaseModel):
    name: str = Field(..., description="Team member name")
    tasksCompleted: int = Field(..., description="Number of completed tasks")
    tasksTotal: int = Field(..., description="Total number of assigned tasks")
    efficiency: int = Field(..., description="Efficiency percentage")

class ProjectPerformanceItem(BaseModel):
    name: str = Field(..., description="Project name")
    progress: int = Field(..., description="Progress percentage")
    tasks: int = Field(..., description="Total number of tasks")
    team: int = Field(..., description="Number of team members")
    status: str = Field(..., description="Project status")
    project_id: str = Field(..., description="Project ID")

class TopContributorItem(BaseModel):
    contributor_name: str = Field(..., description="Contributor name")
    completed_tasks: int = Field(..., description="Number of completed tasks")

class BugSummary(BaseModel):
    open_bugs: int = Field(..., description="Number of open bugs")
    closed_bugs: int = Field(..., description="Number of closed bugs")
    high_severity_bugs: int = Field(..., description="Number of high severity open bugs")

class OverdueTaskItem(BaseModel):
    task_id: str = Field(..., description="Task ID")
    title: str = Field(..., description="Task title")
    assignee: Optional[str] = Field(None, description="Task assignee")
    due_date: str = Field(..., description="Due date")

class UpcomingDeadlineItem(BaseModel):
    task_id: str = Field(..., description="Task ID")
    title: str = Field(..., description="Task title")
    assignee: Optional[str] = Field(None, description="Task assignee")
    due_date: str = Field(..., description="Due date")

class WorkloadDistributionItem(BaseModel):
    assignee_name: str = Field(..., description="Assignee name")
    tasks_total: int = Field(..., description="Total tasks assigned")
    tasks_completed: int = Field(..., description="Completed tasks")
    tasks_pending: int = Field(..., description="Pending tasks")

class DashboardData(BaseModel):
    kpis: KPIData = Field(..., description="Key performance indicators")
    project_status_distribution: List[ProjectStatusItem] = Field(..., description="Project status distribution")
    task_completion_trends: List[TaskCompletionTrendItem] = Field(..., description="Task completion trends over time")
    team_productivity: List[TeamProductivityItem] = Field(..., description="Team member productivity metrics")
    project_performance_summary: List[ProjectPerformanceItem] = Field(..., description="Project performance summary")
    top_contributors: List[TopContributorItem] = Field(..., description="Top contributors leaderboard")
    bug_summary: BugSummary = Field(..., description="Bug insights summary")
    overdue_tasks: List[OverdueTaskItem] = Field(..., description="Overdue tasks list")
    upcoming_deadlines: List[UpcomingDeadlineItem] = Field(..., description="Upcoming deadlines list")
    workload_distribution: List[WorkloadDistributionItem] = Field(..., description="Workload distribution across team members")

# User Dashboard Models
class UserKPIData(BaseModel):
    total_tasks: int = Field(..., description="Total number of tasks assigned to user")
    completed_tasks: int = Field(..., description="Number of completed tasks")
    pending_tasks: int = Field(..., description="Number of pending tasks")
    total_projects: int = Field(..., description="Number of projects user is involved in")

class UserProjectSummaryItem(BaseModel):
    project_id: str = Field(..., description="Project ID")
    project_name: str = Field(..., description="Project name")
    progress_percent: int = Field(..., description="Project progress percentage")
    tasks_total: int = Field(..., description="Total tasks for user in this project")
    tasks_completed: int = Field(..., description="Completed tasks for user in this project")
    tasks_pending: int = Field(..., description="Pending tasks for user in this project")

class UserWorkloadDistribution(BaseModel):
    tasks_total: int = Field(..., description="Total tasks assigned to user")
    tasks_completed: int = Field(..., description="Completed tasks")
    tasks_pending: int = Field(..., description="Pending tasks")

class UserUpcomingDeadlineItem(BaseModel):
    task_id: str = Field(..., description="Task ID")
    title: str = Field(..., description="Task title")
    due_date: str = Field(..., description="Due date")
    project_id: str = Field(..., description="Project ID")

class UserOverdueTaskItem(BaseModel):
    task_id: str = Field(..., description="Task ID")
    title: str = Field(..., description="Task title")
    due_date: str = Field(..., description="Due date")
    project_id: str = Field(..., description="Project ID")

class UserDashboardData(BaseModel):
    kpis: UserKPIData = Field(..., description="User key performance indicators")
    my_project_summary: List[UserProjectSummaryItem] = Field(..., description="User's project summary")
    my_workload_distribution: UserWorkloadDistribution = Field(..., description="User's workload distribution")
    my_upcoming_deadlines: List[UserUpcomingDeadlineItem] = Field(..., description="User's upcoming deadlines")
    my_overdue_tasks: List[UserOverdueTaskItem] = Field(..., description="User's overdue tasks")

class UserDashboardResponse(BaseModel):
    user_id: str = Field(..., description="User ID")
    data: UserDashboardData = Field(..., description="User dashboard data")

class DashboardResponse(BaseModel):
    org_id: str = Field(..., description="Organization ID")
    data: DashboardData = Field(..., description="Dashboard data")
