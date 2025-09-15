from app.core.db.supabase_db import get_supabase_client
from typing import Dict, Any, Optional, List, cast

async def get_dashboard_data(org_id: str) -> Dict[str, Any]:
    """
    Fetch dashboard data for a specific organization from the organization_dashboard_view.
    
    Args:
        org_id: The ID of the organization
        
    Returns:
        A dictionary containing the dashboard data
    """
    supabase = get_supabase_client()
    
    # Query the organization_dashboard_view for the specific organization
    response = supabase.from_("organization_dashboard_view").select("*").eq("org_id", org_id).execute()
    
    # Process the response directly without the handle_db_response function
    result_data = response.data if hasattr(response, 'data') else []
    
    # If no data is found, return an empty result with default structure
    if not result_data:
        return {
            "org_id": org_id,
            "data": {
                "kpis": {
                    "total_tasks": 0,
                    "active_projects": 0,
                    "completed_projects": 0,
                    "blocked_projects": 0,
                    "team_members": 0
                },
                "project_status_distribution": [],
                "task_completion_trends": [],
                "team_productivity": [],
                "project_performance_summary": [],
                "top_contributors": [],
                "bug_summary": {
                    "open_bugs": 0,
                    "closed_bugs": 0,
                    "high_severity_bugs": 0
                },
                "overdue_tasks": [],
                "upcoming_deadlines": [],
                "workload_distribution": []
            }
        }
    
    # Transform the data to match our schema
    dashboard_data = result_data[0]
    
    # Prepare the transformed response
    transformed_data = {
        "org_id": org_id,
        "data": {
            "kpis": dashboard_data.get("kpis", {}),
            "project_status_distribution": _transform_project_status(dashboard_data.get("project_status_distribution", {})),
            "task_completion_trends": _transform_task_trends(dashboard_data.get("task_completion_trends", [])),
            "team_productivity": _transform_team_productivity(dashboard_data.get("team_productivity", [])),
            "project_performance_summary": _transform_project_summary(dashboard_data.get("project_performance_summary", [])),
            "top_contributors": _transform_top_contributors(dashboard_data.get("top_contributors", [])),
            "bug_summary": _transform_bug_summary(dashboard_data.get("bug_summary", {})),
            "overdue_tasks": _transform_overdue_tasks(dashboard_data.get("overdue_tasks", [])),
            "upcoming_deadlines": _transform_upcoming_deadlines(dashboard_data.get("upcoming_deadlines", [])),
            "workload_distribution": _transform_workload_distribution(dashboard_data.get("workload_distribution", []))
        }
    }
    
    return transformed_data

def _transform_project_status(status_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Transform project status distribution data to the required format.
    
    Args:
        status_data: Raw project status data from the database
        
    Returns:
        List of project status items with proper format
    """
    # Define status colors mapping
    status_colors = {
        "active": "#3B82F6",  # Blue
        "completed": "#10B981",  # Green
        "on_hold": "#F59E0B",  # Amber
        "blocked": "#EF4444",  # Red
        "planning": "#8B5CF6",  # Purple
        "not_started": "#6B7280",  # Gray
        "archived": "#1F2937",  # Dark gray
        "in_progress": "#3B82F6"  # Blue (same as active)
    }
    
    result = []
    
    # Convert the JSON object into a list of objects with name, value, and color
    for status, count in status_data.items():
        result.append({
            "name": status.replace("_", " ").title(),
            "value": count,
            "color": status_colors.get(status.lower(), "#6B7280")  # Default to gray if status not found
        })
    
    return result

def _transform_task_trends(trends_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform task completion trends data to match our expected schema.
    
    Args:
        trends_data: Raw task trends data from the database
        
    Returns:
        List of task trend items in the required format
    """
    result = []
    
    for trend in trends_data:
        # Map the database fields to our expected schema
        # The field 'pending' in our schema is equivalent to 'in_progress' + 'on_hold' in the database
        transformed_trend = {
            "month": trend.get("month", ""),
            "completed": trend.get("completed", 0),
            "pending": trend.get("in_progress", 0) + trend.get("on_hold", 0),
            "blocked": trend.get("blocked", 0)
        }
        result.append(transformed_trend)
    
    return result

def _transform_team_productivity(productivity_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform team productivity data to match our expected schema.
    
    Args:
        productivity_data: Raw team productivity data from the database
        
    Returns:
        List of team productivity items in the required format
    """
    result = []
    
    for item in productivity_data:
        # Get assignee name with proper null handling
        assignee_name = item.get("assignee_name")
        if assignee_name is None or assignee_name == "":
            assignee_name = "Unassigned"
        
        # Map the database fields to our expected schema
        transformed_item = {
            "name": str(assignee_name),  # Ensure it's always a string
            "tasksCompleted": int(item.get("tasks_completed", 0)),
            "tasksTotal": int(item.get("tasks_total", 0)),
            "efficiency": int(item.get("productivity_percent", 0))
        }
        result.append(transformed_item)
    
    return result

def _transform_project_summary(summary_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform project performance summary data to match our expected schema.
    
    Args:
        summary_data: Raw project summary data from the database
        
    Returns:
        List of project performance items in the required format
    """
    result = []
    
    for item in summary_data:
        # Map the database fields to our expected schema with null handling
        transformed_item = {
            "name": str(item.get("project_name", "Untitled Project")),
            "progress": int(item.get("progress_percent", 0)),
            "tasks": int(item.get("tasks_total", 0)),
            "team": int(item.get("team_members", 0)),
            "status": str(item.get("status", "Unknown")),
            "project_id": str(item.get("project_id", ""))
        }
        result.append(transformed_item)
    
    return result

def _transform_top_contributors(contributors_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform top contributors data to match our expected schema.
    
    Args:
        contributors_data: Raw top contributors data from the database
        
    Returns:
        List of top contributor items in the required format
    """
    result = []
    
    for item in contributors_data:
        # Get contributor name with proper null handling
        contributor_name = item.get("contributor_name")
        if contributor_name is None or contributor_name == "":
            contributor_name = "Unassigned"
        
        # Map the database fields to our expected schema
        transformed_item = {
            "contributor_name": str(contributor_name),
            "completed_tasks": int(item.get("completed_tasks", 0))
        }
        result.append(transformed_item)
    
    return result

def _transform_bug_summary(bug_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform bug summary data to match our expected schema.
    
    Args:
        bug_data: Raw bug summary data from the database
        
    Returns:
        Bug summary object in the required format
    """
    return {
        "open_bugs": int(bug_data.get("open_bugs", 0) or 0),
        "closed_bugs": int(bug_data.get("closed_bugs", 0) or 0),
        "high_severity_bugs": int(bug_data.get("high_severity_bugs", 0) or 0)
    }

def _transform_overdue_tasks(overdue_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform overdue tasks data to match our expected schema.
    
    Args:
        overdue_data: Raw overdue tasks data from the database
        
    Returns:
        List of overdue task items in the required format
    """
    result = []
    
    for item in overdue_data:
        # Map the database fields to our expected schema with null handling
        transformed_item = {
            "task_id": str(item.get("task_id", "")),
            "title": str(item.get("title", "Untitled Task")),
            "assignee": str(item.get("assignee", "")) if item.get("assignee") else None,
            "due_date": str(item.get("due_date", ""))
        }
        result.append(transformed_item)
    
    return result

def _transform_upcoming_deadlines(deadlines_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform upcoming deadlines data to match our expected schema.
    
    Args:
        deadlines_data: Raw upcoming deadlines data from the database
        
    Returns:
        List of upcoming deadline items in the required format
    """
    result = []
    
    for item in deadlines_data:
        # Map the database fields to our expected schema with null handling
        transformed_item = {
            "task_id": str(item.get("task_id", "")),
            "title": str(item.get("title", "Untitled Task")),
            "assignee": str(item.get("assignee", "")) if item.get("assignee") else None,
            "due_date": str(item.get("due_date", ""))
        }
        result.append(transformed_item)
    
    return result

def _transform_workload_distribution(workload_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform workload distribution data to match our expected schema.
    
    Args:
        workload_data: Raw workload distribution data from the database
        
    Returns:
        List of workload distribution items in the required format
    """
    result = []
    
    for item in workload_data:
        # Get assignee name with proper null handling
        assignee_name = item.get("assignee_name")
        if assignee_name is None or assignee_name == "":
            assignee_name = "Unassigned"
        
        # Map the database fields to our expected schema
        transformed_item = {
            "assignee_name": str(assignee_name),
            "tasks_total": int(item.get("tasks_total", 0)),
            "tasks_completed": int(item.get("tasks_completed", 0)),
            "tasks_pending": int(item.get("tasks_pending", 0))
        }
        result.append(transformed_item)
    
    return result


async def get_user_dashboard_data(user_id: str) -> Dict[str, Any]:
    """
    Fetch dashboard data for a specific user from the user_dashboard_view.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        A dictionary containing the user dashboard data
    """
    supabase = get_supabase_client()
    
    # Query the user_dashboard_view for the specific user
    response = supabase.from_("user_dashboard_view").select("*").eq("user_id", user_id).execute()
    
    # Process the response directly without the handle_db_response function
    result_data = response.data if hasattr(response, 'data') else []
    
    # If no data is found, return an empty result with default structure
    if not result_data:
        return {
            "user_id": user_id,
            "data": {
                "kpis": {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "pending_tasks": 0,
                    "total_projects": 0
                },
                "my_project_summary": [],
                "my_workload_distribution": {
                    "tasks_total": 0,
                    "tasks_completed": 0,
                    "tasks_pending": 0
                },
                "my_upcoming_deadlines": [],
                "my_overdue_tasks": []
            }
        }
    
    # Transform the data to match our schema
    user_dashboard_data = result_data[0]
    
    # Prepare the transformed response
    transformed_data = {
        "user_id": user_id,
        "data": {
            "kpis": _transform_user_kpis(user_dashboard_data.get("kpis", {})),
            "my_project_summary": _transform_user_project_summary(user_dashboard_data.get("my_project_summary", [])),
            "my_workload_distribution": _transform_user_workload_distribution(user_dashboard_data.get("my_workload_distribution", {})),
            "my_upcoming_deadlines": _transform_user_upcoming_deadlines(user_dashboard_data.get("my_upcoming_deadlines", [])),
            "my_overdue_tasks": _transform_user_overdue_tasks(user_dashboard_data.get("my_overdue_tasks", []))
        }
    }
    
    return transformed_data


def _transform_user_kpis(kpis_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform user KPIs data to match our expected schema."""
    return {
        "total_tasks": int(kpis_data.get("total_tasks", 0) or 0),
        "completed_tasks": int(kpis_data.get("completed_tasks", 0) or 0),
        "pending_tasks": int(kpis_data.get("pending_tasks", 0) or 0),
        "total_projects": int(kpis_data.get("total_projects", 0) or 0)
    }


def _transform_user_project_summary(project_summary_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform user project summary data to match our expected schema."""
    result = []
    
    for item in project_summary_data:
        transformed_item = {
            "project_id": str(item.get("project_id", "")),
            "project_name": str(item.get("project_name", "Untitled Project")),
            "progress_percent": int(item.get("progress_percent", 0) or 0),
            "tasks_total": int(item.get("tasks_total", 0) or 0),
            "tasks_completed": int(item.get("tasks_completed", 0) or 0),
            "tasks_pending": int(item.get("tasks_pending", 0) or 0)
        }
        result.append(transformed_item)
    
    return result


def _transform_user_workload_distribution(workload_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform user workload distribution data to match our expected schema."""
    return {
        "tasks_total": int(workload_data.get("tasks_total", 0) or 0),
        "tasks_completed": int(workload_data.get("tasks_completed", 0) or 0),
        "tasks_pending": int(workload_data.get("tasks_pending", 0) or 0)
    }


def _transform_user_upcoming_deadlines(deadlines_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform user upcoming deadlines data to match our expected schema."""
    result = []
    
    for item in deadlines_data:
        transformed_item = {
            "task_id": str(item.get("task_id", "")),
            "title": str(item.get("title", "Untitled Task")),
            "due_date": str(item.get("due_date", "")),
            "project_id": str(item.get("project_id", ""))
        }
        result.append(transformed_item)
    
    return result


def _transform_user_overdue_tasks(overdue_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform user overdue tasks data to match our expected schema."""
    result = []
    
    for item in overdue_data:
        transformed_item = {
            "task_id": str(item.get("task_id", "")),
            "title": str(item.get("title", "Untitled Task")),
            "due_date": str(item.get("due_date", "")),
            "project_id": str(item.get("project_id", ""))
        }
        result.append(transformed_item)
    
    return result