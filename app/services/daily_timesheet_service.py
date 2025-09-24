from typing import Dict, Any, List, Optional
from datetime import date, datetime
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from fastapi import HTTPException
from app.models.schemas.daily_timesheet import (
    DailyTimesheetCreate, 
    DailyTimesheetUpdate, 
    DailyTimesheetFilters
)

async def get_user_details_from_org(supabase, org_id: str, user_id: str) -> Dict[str, Any]:
    """Helper function to get user details from organization_members"""
    try:
        def op():
            return supabase.from_("organization_members").select("""
                username,
                email,
                designation
            """).eq("org_id", org_id).eq("user_id", user_id).single().execute()
        
        result = await safe_supabase_operation(op, "Failed to fetch user details")
        return result.data if result.data else {}
    except:
        return {}

async def create_or_update_daily_timesheet(data: DailyTimesheetCreate, user_id: str) -> Dict[str, Any]:
    """
    Create or update a daily timesheet entry.
    Uses upsert to handle both create and update operations.
    """
    supabase = get_supabase_client()
    
    # Prepare the data for database insertion
    timesheet_data = {
        "org_id": data.org_id,
        "project_id": data.project_id,
        "user_id": data.user_id,
        "entry_date": data.entry_date.isoformat() if hasattr(data.entry_date, 'isoformat') else str(data.entry_date),
        "in_progress": data.in_progress,
        "completed": data.completed,
        "blocked": data.blocked,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Remove None values to avoid overwriting existing data with null
    timesheet_data = {k: v for k, v in timesheet_data.items() if v is not None}
    
    def op():
        return supabase.from_("daily_timesheets").upsert(
            timesheet_data,
            on_conflict="org_id,project_id,user_id,entry_date"
        ).execute()
    
    result = await safe_supabase_operation(op, "Failed to create/update daily timesheet")
    return result

async def get_daily_timesheet(
    org_id: str, 
    project_id: str, 
    user_id: str, 
    entry_date: date
) -> Dict[str, Any]:
    """Get a specific daily timesheet entry."""
    supabase = get_supabase_client()
    
    date_str = entry_date.isoformat() if hasattr(entry_date, 'isoformat') else str(entry_date)
    
    def op():
        return supabase.from_("daily_timesheets").select("*").eq(
            "org_id", org_id
        ).eq(
            "project_id", project_id
        ).eq(
            "user_id", user_id
        ).eq(
            "entry_date", date_str
        ).single().execute()
    
    result = await safe_supabase_operation(op, "Failed to fetch daily timesheet")
    return result

async def get_daily_timesheets_by_filters(filters: DailyTimesheetFilters) -> Dict[str, Any]:
    """
    Get daily timesheets based on provided filters.
    Returns timesheets with user and project details.
    """
    supabase = get_supabase_client()
    
    def op():
        # Build the query with joins to get user and project details
        query = supabase.from_("daily_timesheets").select("""
            *,
            projects!inner(
                name
            )
        """).eq("org_id", filters.org_id)
        
        # Apply project filter
        if filters.project_ids:
            query = query.in_("project_id", filters.project_ids)
        
        # Apply user filter
        if filters.user_ids:
            query = query.in_("user_id", filters.user_ids)
        
        # Apply date range filters
        if filters.date_from:
            date_from_str = filters.date_from.isoformat() if hasattr(filters.date_from, 'isoformat') else str(filters.date_from)
            query = query.gte("entry_date", date_from_str)
        
        if filters.date_to:
            date_to_str = filters.date_to.isoformat() if hasattr(filters.date_to, 'isoformat') else str(filters.date_to)
            query = query.lte("entry_date", date_to_str)
        
        # Order by date descending, then by user
        query = query.order("entry_date", desc=True).order("user_id")
        
        return query.execute()
    
    result = await safe_supabase_operation(op, "Failed to fetch daily timesheets")
    
    # Transform the result to include user and project details
    if result.data:
        transformed_data = []
        for item in result.data:
            project = item.get("projects", {})
            
            # Get user details from organization_members separately
            user_details = await get_user_details_from_org(supabase, filters.org_id, item.get("user_id"))
            
            transformed_item = {
                **item,
                "user_name": user_details.get("username") or user_details.get("email", "").split("@")[0],
                "user_email": user_details.get("email"),
                "user_designation": user_details.get("designation"),
                "project_name": project.get("name")
            }
            
            # Clean up the nested objects
            transformed_item.pop("projects", None)
            
            transformed_data.append(transformed_item)
        
        result.data = transformed_data
    
    return result

async def get_user_timesheets_for_date_range(
    org_id: str,
    user_id: str,
    date_from: date,
    date_to: date
) -> Dict[str, Any]:
    """Get all timesheets for a specific user within a date range."""
    supabase = get_supabase_client()
    
    date_from_str = date_from.isoformat() if hasattr(date_from, 'isoformat') else str(date_from)
    date_to_str = date_to.isoformat() if hasattr(date_to, 'isoformat') else str(date_to)
    
    def op():
        return supabase.from_("daily_timesheets").select("""
            *,
            projects!inner(name)
        """).eq(
            "org_id", org_id
        ).eq(
            "user_id", user_id
        ).gte(
            "entry_date", date_from_str
        ).lte(
            "entry_date", date_to_str
        ).order("entry_date", desc=True).execute()
    
    result = await safe_supabase_operation(op, "Failed to fetch user timesheets")
    return result

async def delete_daily_timesheet(
    org_id: str,
    project_id: str,
    user_id: str,
    entry_date: date
) -> Dict[str, Any]:
    """Delete a specific daily timesheet entry."""
    supabase = get_supabase_client()
    
    date_str = entry_date.isoformat() if hasattr(entry_date, 'isoformat') else str(entry_date)
    
    def op():
        return supabase.from_("daily_timesheets").delete().eq(
            "org_id", org_id
        ).eq(
            "project_id", project_id
        ).eq(
            "user_id", user_id
        ).eq(
            "entry_date", date_str
        ).execute()
    
    result = await safe_supabase_operation(op, "Failed to delete daily timesheet")
    return result

async def bulk_create_or_update_timesheets(
    timesheets: List[DailyTimesheetCreate],
    user_id: str
) -> Dict[str, Any]:
    """
    Bulk create or update multiple timesheet entries.
    Useful for batch operations or importing data.
    """
    supabase = get_supabase_client()
    
    # Prepare all timesheet data
    timesheet_data_list = []
    for timesheet in timesheets:
        data = {
            "org_id": timesheet.org_id,
            "project_id": timesheet.project_id,
            "user_id": timesheet.user_id,
            "entry_date": timesheet.entry_date.isoformat() if hasattr(timesheet.entry_date, 'isoformat') else str(timesheet.entry_date),
            "in_progress": timesheet.in_progress,
            "completed": timesheet.completed,
            "blocked": timesheet.blocked,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        timesheet_data_list.append(data)
    
    def op():
        return supabase.from_("daily_timesheets").upsert(
            timesheet_data_list,
            on_conflict="org_id,project_id,user_id,entry_date"
        ).execute()
    
    result = await safe_supabase_operation(op, "Failed to bulk create/update daily timesheets")
    return result

async def get_team_timesheets_summary(
    org_id: str,
    entry_date: date,
    project_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get a comprehensive team timesheets summary for a specific date.
    Fetches all projects and their members first, then overlays timesheet data.
    """
    supabase = get_supabase_client()
    
    # Import services for fetching projects and members
    from app.services.project_service import get_all_org_projects
    from app.services.organization_member_service import get_members_for_org
    from app.services.project_member_service import get_members_for_project
    
    date_str = entry_date.isoformat() if hasattr(entry_date, 'isoformat') else str(entry_date)
    
    # 1. Fetch all projects in the organization
    projects_cards = await get_all_org_projects(org_id)
    
    # Filter projects if project_ids is provided
    if project_ids:
        projects_cards = [p for p in projects_cards if p.project_id in project_ids]
    
    # 2. Fetch all organization members
    org_members = await get_members_for_org(org_id, limit=100000)
    org_member_by_id = {str(m.get("user_id")): m for m in org_members if m.get("user_id")}
    
    # 3. Fetch project members for each project
    project_members_map = {}
    for project in projects_cards:
        project_members = await get_members_for_project(project.project_id, limit=100000)
        project_members_map[project.project_id] = {str(m.get("user_id")): m for m in project_members if m.get("user_id")}
    
    # 4. Fetch timesheet data for the specific date
    def timesheet_op():
        query = supabase.from_("daily_timesheets").select("""
            user_id,
            project_id,
            in_progress,
            completed,
            blocked
        """).eq("org_id", org_id).eq("entry_date", date_str)
        
        if project_ids:
            query = query.in_("project_id", project_ids)
        
        return query.execute()
    
    timesheet_result = await safe_supabase_operation(timesheet_op, "Failed to fetch team timesheets summary")
    
    # Create timesheet data map for quick lookup
    timesheet_by_user_project = {}
    for item in (timesheet_result.data or []):
        key = f"{item['user_id']}_{item['project_id']}"
        timesheet_by_user_project[key] = item
    
    # 5. Build comprehensive project structure with members and timesheet data
    projects_with_members = []
    
    for project_card in projects_cards:
        project_info = {
            "project_id": project_card.project_id,
            "project_name": project_card.name,
            "description": project_card.description,
            "owner": project_card.owner,
            "team_members": project_card.team_members,
            "members": []
        }
        
        # Get all members for this project
        project_member_ids = project_members_map.get(project_card.project_id, {}).keys()
        
        for user_id in project_member_ids:
            # Get organization member details
            org_member = org_member_by_id.get(str(user_id), {})
            project_member = project_members_map[project_card.project_id].get(str(user_id), {})
            
            # Get timesheet data for this user and project
            timesheet_key = f"{user_id}_{project_card.project_id}"
            timesheet_data = timesheet_by_user_project.get(timesheet_key, {})
            
            member_info = {
                "user_id": str(user_id),
                "name": org_member.get("username") or org_member.get("email", "").split("@")[0] if org_member.get("email") else f"User {user_id}",
                "email": org_member.get("email", ""),
                "designation": org_member.get("designation") or project_member.get("designation"),
                "avatar_initials": (org_member.get("username") or org_member.get("email", "") or str(user_id))[:2].upper(),
                "role": project_member.get("role", "member"),
                "org_role": org_member.get("role", "member"),
                "total_hours_today": 0,  # Placeholder for future enhancement
                "total_hours_week": 0,   # Placeholder for future enhancement
                "in_progress": [],
                "completed": [],
                "blockers": []
            }
            
            # Parse timesheet data into structured format
            if timesheet_data.get("in_progress"):
                for line in timesheet_data["in_progress"].split("\n"):
                    if line.strip():
                        member_info["in_progress"].append({
                            "id": f"ip-{len(member_info['in_progress'])}",
                            "title": line.strip().lstrip("• "),
                            "project": project_card.name,
                            "hours_logged": 0  # Placeholder
                        })
            
            if timesheet_data.get("completed"):
                for line in timesheet_data["completed"].split("\n"):
                    if line.strip():
                        member_info["completed"].append({
                            "id": f"comp-{len(member_info['completed'])}",
                            "title": line.strip().lstrip("• "),
                            "project": project_card.name,
                            "hours_logged": 0  # Placeholder
                        })
            
            if timesheet_data.get("blocked"):
                for line in timesheet_data["blocked"].split("\n"):
                    if line.strip():
                        member_info["blockers"].append({
                            "id": f"block-{len(member_info['blockers'])}",
                            "title": line.strip().lstrip("• "),
                            "project": project_card.name,
                            "blocked_reason": "See timesheet notes"
                        })
            
            project_info["members"].append(member_info)
        
        projects_with_members.append(project_info)
    
    # 6. Create a comprehensive flat list of ALL organization members (not just project members)
    all_users = []
    user_summaries = {}
    
    # First, initialize all org members with their basic info and empty timesheet data
    for org_member in org_members:
        user_id = str(org_member.get("user_id"))
        if user_id:
            user_summaries[user_id] = {
                "user_id": user_id,
                "name": org_member.get("username") or org_member.get("email", "").split("@")[0] if org_member.get("email") else f"User {user_id}",
                "email": org_member.get("email", ""),
                "designation": org_member.get("designation"),
                "avatar_initials": (org_member.get("username") or org_member.get("email", "") or str(user_id))[:2].upper(),
                "role": org_member.get("role", "member"),
                "total_hours_today": 0,
                "total_hours_week": 0,
                "in_progress": [],
                "completed": [],
                "blockers": []
            }
    
    # Then, overlay project-specific timesheet data for members who have project assignments
    for project in projects_with_members:
        for member in project["members"]:
            user_id = member["user_id"]
            
            if user_id in user_summaries:
                # Aggregate tasks from all projects for this user
                user_summaries[user_id]["in_progress"].extend(member["in_progress"])
                user_summaries[user_id]["completed"].extend(member["completed"])
                user_summaries[user_id]["blockers"].extend(member["blockers"])
    
    # Finally, check for any direct timesheet entries for users not assigned to projects
    # This handles cases where users might have timesheet data but no project assignments
    for timesheet_entry in (timesheet_result.data or []):
        user_id = str(timesheet_entry.get("user_id"))
        if user_id in user_summaries:
            # Check if this user already has data from project assignments
            has_existing_data = (
                len(user_summaries[user_id]["in_progress"]) > 0 or
                len(user_summaries[user_id]["completed"]) > 0 or
                len(user_summaries[user_id]["blockers"]) > 0
            )
            
            # If no existing project-based data, add direct timesheet data
            if not has_existing_data:
                # Parse direct timesheet data
                if timesheet_entry.get("in_progress"):
                    for line in timesheet_entry["in_progress"].split("\n"):
                        if line.strip():
                            user_summaries[user_id]["in_progress"].append({
                                "id": f"ip-{len(user_summaries[user_id]['in_progress'])}",
                                "title": line.strip().lstrip("• "),
                                "project": "General",
                                "hours_logged": 0
                            })
                
                if timesheet_entry.get("completed"):
                    for line in timesheet_entry["completed"].split("\n"):
                        if line.strip():
                            user_summaries[user_id]["completed"].append({
                                "id": f"comp-{len(user_summaries[user_id]['completed'])}",
                                "title": line.strip().lstrip("• "),
                                "project": "General",
                                "hours_logged": 0
                            })
                
                if timesheet_entry.get("blocked"):
                    for line in timesheet_entry["blocked"].split("\n"):
                        if line.strip():
                            user_summaries[user_id]["blockers"].append({
                                "id": f"block-{len(user_summaries[user_id]['blockers'])}",
                                "title": line.strip().lstrip("• "),
                                "project": "General",
                                "blocked_reason": "See timesheet notes"
                            })
    
    all_users = list(user_summaries.values())
    
    # Return in the expected format with .data attribute
    class ResultObject:
        def __init__(self, data):
            self.data = data
    
    return ResultObject({
        "users": all_users,
        "projects": projects_with_members,
        "date": date_str,
        "org_id": org_id
    })
