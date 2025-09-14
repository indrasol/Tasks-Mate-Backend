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
        # Map the database fields to our expected schema
        transformed_item = {
            "name": item.get("assignee_name", "Unknown"),
            "tasksCompleted": item.get("tasks_completed", 0),
            "tasksTotal": item.get("tasks_total", 0),
            "efficiency": item.get("productivity_percent", 0)
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
        # Map the database fields to our expected schema
        transformed_item = {
            "name": item.get("project_name", "Unknown"),
            "progress": item.get("progress_percent", 0),
            "tasks": item.get("tasks_total", 0),
            "team": item.get("team_members", 0),
            "status": item.get("status", "Unknown"),
            "project_id": item.get("project_id", "")
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
        # Map the database fields to our expected schema
        transformed_item = {
            "contributor_name": item.get("contributor_name", "Unknown"),
            "completed_tasks": item.get("completed_tasks", 0)
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
        "open_bugs": bug_data.get("open_bugs", 0),
        "closed_bugs": bug_data.get("closed_bugs", 0),
        "high_severity_bugs": bug_data.get("high_severity_bugs", 0)
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
        # Map the database fields to our expected schema
        transformed_item = {
            "task_id": item.get("task_id", ""),
            "title": item.get("title", "Unknown"),
            "assignee": item.get("assignee"),
            "due_date": item.get("due_date", "")
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
        # Map the database fields to our expected schema
        transformed_item = {
            "task_id": item.get("task_id", ""),
            "title": item.get("title", "Unknown"),
            "assignee": item.get("assignee"),
            "due_date": item.get("due_date", "")
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
        # Map the database fields to our expected schema
        transformed_item = {
            "assignee_name": item.get("assignee_name", "Unknown"),
            "tasks_total": item.get("tasks_total", 0),
            "tasks_completed": item.get("tasks_completed", 0),
            "tasks_pending": item.get("tasks_pending", 0)
        }
        result.append(transformed_item)
    
    return result