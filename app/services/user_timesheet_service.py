from typing import Dict, Any, List, Optional
from datetime import date, datetime
import json
import uuid
import logging
import calendar as cal
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from app.models.schemas.user_timesheet import TimesheetEntry

# Set up logging
logger = logging.getLogger(__name__)

class UserTimesheetService:
    """Service class for user timesheet operations"""
    
    @staticmethod
    async def create_or_update_timesheet_field(
        org_id: str,
        user_id: str,
        entry_date: date,
        field_type: str,
        field_content: str
    ) -> Dict[str, Any]:
        """
        Create or update a specific field in user's timesheet.
        
        Args:
            org_id: Organization ID
            user_id: User ID
            entry_date: Date for the timesheet entry
            field_type: 'in_progress', 'completed', or 'blocked'
            field_content: Text content for the field
            
        Returns:
            Dict containing operation result
        """
        supabase = get_supabase_client()
        date_str = entry_date.isoformat()
        
        try:
            # Get existing timesheet - use limit(1) instead of single() to handle 0 rows gracefully
            def get_existing():
                return supabase.from_("user_daily_timesheets").select("*").eq(
                    "org_id", org_id
                ).eq("user_id", user_id).eq("entry_date", date_str).limit(1).execute()
            
            existing_result = await safe_supabase_operation(get_existing, "Failed to fetch existing timesheet")
            
            # Parse field content into structured entries
            field_entries = UserTimesheetService._parse_text_to_entries(field_content, field_type)
            
            # Check if existing timesheet record exists
            if existing_result.data and len(existing_result.data) > 0:
                # Update existing timesheet
                existing_record = existing_result.data[0]  # Get the first (and only) record
                existing_data = existing_record.get('timesheet_data', {})
                
                # Update the specific field
                if field_entries:
                    existing_data[field_type] = field_entries
                else:
                    # Remove field if content is empty
                    existing_data.pop(field_type, None)
                
                def update_op():
                    return supabase.from_("user_daily_timesheets").update({
                        'timesheet_data': existing_data,
                        'updated_at': datetime.utcnow().isoformat()
                    }).eq('id', existing_record['id']).execute()
                
                result = await safe_supabase_operation(update_op, "Failed to update timesheet")
                
            else:
                # Create new timesheet
                timesheet_data = {}
                if field_entries:
                    timesheet_data[field_type] = field_entries
                
                def create_op():
                    return supabase.from_("user_daily_timesheets").insert({
                        'org_id': org_id,
                        'user_id': user_id,
                        'entry_date': date_str,
                        'timesheet_data': timesheet_data
                    }).execute()
                
                result = await safe_supabase_operation(create_op, "Failed to create timesheet")
            
            logger.info(f"Successfully updated timesheet field {field_type} for user {user_id} on {date_str}")
            return result
            
        except Exception as e:
            logger.error(f"Error updating timesheet field: {str(e)}")
            raise Exception(f"Failed to update timesheet field: {str(e)}")

    @staticmethod
    async def get_user_timesheet_for_date(
        org_id: str,
        user_id: str,
        entry_date: date
    ) -> Dict[str, Any]:
        """
        Get user's timesheet for a specific date.
        
        Args:
            org_id: Organization ID
            user_id: User ID  
            entry_date: Date to fetch timesheet for
            
        Returns:
            Dict containing timesheet data or empty structure
        """
        supabase = get_supabase_client()
        date_str = entry_date.isoformat()
        
        try:
            def get_op():
                return supabase.from_("user_daily_timesheets").select("*").eq(
                    "org_id", org_id
                ).eq("user_id", user_id).eq("entry_date", date_str).limit(1).execute()
            
            result = await safe_supabase_operation(get_op, "Failed to fetch user timesheet")
            
            if result.data and len(result.data) > 0:
                return {'data': result.data[0]}
            else:
                # Return empty structure for consistency
                empty_data = {
                    'org_id': org_id,
                    'user_id': user_id,
                    'entry_date': date_str,
                    'timesheet_data': {
                        'in_progress': [],
                        'completed': [],
                        'blocked': []
                    },
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                return {'data': empty_data}
                
        except Exception as e:
            logger.error(f"Error fetching user timesheet: {str(e)}")
            raise Exception(f"Failed to fetch user timesheet: {str(e)}")

    @staticmethod
    async def get_team_timesheets_for_date(
        org_id: str,
        entry_date: date,
        user_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get all team timesheets for a specific date.
        
        Args:
            org_id: Organization ID
            entry_date: Date to fetch timesheets for
            user_ids: Optional list of specific user IDs to filter
            
        Returns:
            Dict containing team timesheet data
        """
        supabase = get_supabase_client()
        date_str = entry_date.isoformat()
        
        try:
            # Get organization members
            from app.services.organization_member_service import get_members_for_org
            org_members_raw = await get_members_for_org(org_id, limit=100000)
            
            # Ensure we have valid member dictionaries and filter out invalid ones
            org_members = []
            for member in (org_members_raw or []):
                if isinstance(member, dict) and member.get('user_id'):
                    org_members.append(member)
                else:
                    logger.warning(f"Invalid member data: {type(member)} - {member}")
            
            # Filter by user_ids if provided
            if user_ids:
                org_members = [m for m in org_members if str(m.get('user_id')) in user_ids]
            
            # Get timesheet data for the date
            def get_timesheets():
                query = supabase.from_("user_daily_timesheets").select("*").eq(
                    "org_id", org_id
                ).eq("entry_date", date_str)
                
                if user_ids:
                    query = query.in_("user_id", user_ids)
                    
                return query.execute()
            
            timesheets_result = await safe_supabase_operation(get_timesheets, "Failed to fetch team timesheets")
            
            # Create lookup for timesheet data
            timesheet_by_user = {}
            for ts in (timesheets_result.data or []):
                if isinstance(ts, dict) and 'user_id' in ts:
                    timesheet_by_user[ts['user_id']] = ts
                else:
                    logger.warning(f"Invalid timesheet data: {type(ts)} - {ts}")
            
            # Build team data with proper structure
            team_data = []
            for member in org_members:
                try:
                    if not isinstance(member, dict):
                        logger.warning(f"Skipping invalid member: {type(member)} - {member}")
                        continue
                        
                    user_id = str(member.get('user_id', ''))
                    if not user_id:
                        logger.warning(f"Skipping member without user_id: {member}")
                        continue
                        
                    timesheet = timesheet_by_user.get(user_id)
                    
                    # Build user data structure with safe access
                    user_data = {
                        'user_id': user_id,
                        'name': member.get('username') or (member.get('email', '').split('@')[0] if member.get('email') else f'User {user_id}'),
                        'email': member.get('email', ''),
                        'designation': member.get('designation', 'Team Member'),
                        'avatar_initials': UserTimesheetService._get_initials(member),
                        'role': member.get('role', 'member'),
                        'in_progress': [],
                        'completed': [],
                        'blocked': []
                    }
                    
                    # Add timesheet data if exists
                    if timesheet and isinstance(timesheet, dict) and timesheet.get('timesheet_data'):
                        timesheet_data = timesheet.get('timesheet_data', {})
                        if isinstance(timesheet_data, dict):
                            user_data.update({
                                'in_progress': timesheet_data.get('in_progress', []),
                                'completed': timesheet_data.get('completed', []),
                                'blocked': timesheet_data.get('blocked', [])
                            })
                    
                    team_data.append(user_data)
                    
                except Exception as member_error:
                    logger.error(f"Error processing member {member}: {str(member_error)}")
                    continue
            
            logger.info(f"Successfully fetched team timesheets for {len(team_data)} users on {date_str}")
            return {
                'data': {
                    'users': team_data,
                    'date': date_str,
                    'org_id': org_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching team timesheets: {str(e)}")
            raise Exception(f"Failed to fetch team timesheets: {str(e)}")

    @staticmethod
    async def get_calendar_month_status(
        org_id: str,
        year: int,
        month: int,
        user_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get calendar status for a month to show indicators.
        
        Args:
            org_id: Organization ID
            year: Year
            month: Month (1-12)
            user_ids: Optional list of user IDs to filter
            
        Returns:
            Dict containing calendar status data
        """
        supabase = get_supabase_client()
        
        try:
            # Calculate month date range
            first_day = date(year, month, 1)
            last_day = date(year, month, cal.monthrange(year, month)[1])
            
            def get_status():
                query = supabase.from_("user_daily_timesheets").select("""
                    entry_date,
                    user_id,
                    has_data
                """).eq("org_id", org_id).gte(
                    "entry_date", first_day.isoformat()
                ).lte(
                    "entry_date", last_day.isoformat()
                ).eq("has_data", True)
                
                if user_ids:
                    query = query.in_("user_id", user_ids)
                    
                return query.execute()
            
            result = await safe_supabase_operation(get_status, "Failed to fetch calendar status")
            
            # Process results into calendar format
            calendar_status = {}
            for item in (result.data or []):
                if not isinstance(item, dict):
                    logger.warning(f"Invalid calendar status item: {type(item)} - {item}")
                    continue
                    
                entry_date = item.get('entry_date')
                user_id = item.get('user_id')
                
                if not entry_date or not user_id:
                    logger.warning(f"Missing entry_date or user_id in calendar status item: {item}")
                    continue
                    
                if entry_date not in calendar_status:
                    calendar_status[entry_date] = {
                        'hasData': False,
                        'userCount': 0,
                        'users': set()
                    }
                
                calendar_status[entry_date]['hasData'] = True
                calendar_status[entry_date]['users'].add(str(user_id))
            
            # Convert sets to counts and clean up
            for date_key in calendar_status:
                calendar_status[date_key]['userCount'] = len(calendar_status[date_key]['users'])
                del calendar_status[date_key]['users']
            
            logger.info(f"Successfully fetched calendar status for {year}-{month:02d}")
            return {
                'calendar_status': calendar_status,
                'year': year,
                'month': month,
                'org_id': org_id
            }
            
        except Exception as e:
            logger.error(f"Error fetching calendar status: {str(e)}")
            raise Exception(f"Failed to fetch calendar status: {str(e)}")

    @staticmethod
    async def delete_user_timesheet(
        org_id: str,
        user_id: str,
        entry_date: date
    ) -> Dict[str, Any]:
        """
        Delete a user's timesheet for a specific date.
        
        Args:
            org_id: Organization ID
            user_id: User ID
            entry_date: Date of timesheet to delete
            
        Returns:
            Dict containing operation result
        """
        supabase = get_supabase_client()
        date_str = entry_date.isoformat()
        
        try:
            def delete_op():
                return supabase.from_("user_daily_timesheets").delete().eq(
                    "org_id", org_id
                ).eq("user_id", user_id).eq("entry_date", date_str).execute()
            
            result = await safe_supabase_operation(delete_op, "Failed to delete timesheet")
            
            logger.info(f"Successfully deleted timesheet for user {user_id} on {date_str}")
            return result
            
        except Exception as e:
            logger.error(f"Error deleting timesheet: {str(e)}")
            raise Exception(f"Failed to delete timesheet: {str(e)}")

    # Private helper methods
    @staticmethod
    def _parse_text_to_entries(text_content: str, field_type: str) -> List[Dict[str, Any]]:
        """
        Convert text content to structured timesheet entries.
        
        Args:
            text_content: Raw text input from user
            field_type: Type of field ('in_progress', 'completed', 'blocked')
            
        Returns:
            List of structured entry dictionaries
        """
        if not text_content or not text_content.strip():
            return []
        
        entries = []
        lines = [line.strip() for line in text_content.strip().split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            # Clean up bullet points and common prefixes
            clean_line = line.replace('•', '').replace('-', '').replace('*', '').strip()
            if not clean_line:
                continue
                
            # Create entry with unique ID
            entry = {
                'id': f'{field_type}_{uuid.uuid4().hex[:8]}',
                'title': clean_line[:500],  # Limit title length
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Add field-specific timestamps
            if field_type == 'completed':
                entry['completed_at'] = datetime.utcnow().isoformat()
            elif field_type == 'blocked':
                entry['blocked_since'] = datetime.utcnow().isoformat()
                
            entries.append(entry)
        
        return entries

    @staticmethod
    def _get_initials(member: Dict[str, Any]) -> str:
        """
        Get user initials from member data.
        
        Args:
            member: Member data dictionary
            
        Returns:
            Two-character initials string
        """
        try:
            if not isinstance(member, dict):
                return '??'
                
            name = member.get('username') or member.get('email', '') or str(member.get('user_id', ''))
            if not name:
                return '??'
                
            if '@' in name:
                name = name.split('@')[0]
            
            # Get first two characters, uppercase
            initials = name[:2].upper() if name else '??'
            return initials if len(initials) == 2 else initials + '?'
        except Exception:
            return '??'

# Convenience functions for backward compatibility
async def create_or_update_user_timesheet_field(
    org_id: str,
    user_id: str,
    entry_date: date,
    field_type: str,
    field_content: str
) -> Dict[str, Any]:
    """Wrapper function for the service method"""
    return await UserTimesheetService.create_or_update_timesheet_field(
        org_id, user_id, entry_date, field_type, field_content
    )

async def get_user_timesheet_for_date(
    org_id: str,
    user_id: str,
    entry_date: date
) -> Dict[str, Any]:
    """Wrapper function for the service method"""
    return await UserTimesheetService.get_user_timesheet_for_date(org_id, user_id, entry_date)

async def get_team_timesheets_for_date(
    org_id: str,
    entry_date: date,
    user_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Wrapper function for the service method"""
    return await UserTimesheetService.get_team_timesheets_for_date(org_id, entry_date, user_ids)

async def get_calendar_month_status(
    org_id: str,
    year: int,
    month: int,
    user_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Wrapper function for the service method"""
    return await UserTimesheetService.get_calendar_month_status(org_id, year, month, user_ids)

async def delete_user_timesheet(
    org_id: str,
    user_id: str,
    entry_date: date
) -> Dict[str, Any]:
    """Wrapper function for the service method"""
    return await UserTimesheetService.delete_user_timesheet(org_id, user_id, entry_date)
