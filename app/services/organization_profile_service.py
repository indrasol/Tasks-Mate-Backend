from typing import Dict, Any, Optional
import json
import uuid
import logging
from datetime import datetime

from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
from app.models.schemas.organization_profile import (
    OrganizationProfileCreate, 
    OrganizationProfileUpdate,
    CoreValue
)

# Set up logging
logger = logging.getLogger(__name__)

class OrganizationProfileService:
    """Service class for organization profile operations"""
    
    @staticmethod
    async def get_organization_profile(org_id: str) -> Dict[str, Any]:
        """
        Get organization profile by org_id.
        
        Args:
            org_id: Organization ID
            
        Returns:
            Dict containing profile data or default structure
        """
        supabase = get_supabase_client()
        
        try:
            def get_op():
                return supabase.from_("organization_profile").select("*").eq(
                    "org_id", org_id
                ).limit(1).execute()
            
            result = await safe_supabase_operation(get_op, "Failed to fetch organization profile")
            
            if result.data and len(result.data) > 0:
                profile_data = result.data[0]
                
                # Parse core_values JSON if it exists
                if profile_data.get('core_values'):
                    try:
                        if isinstance(profile_data['core_values'], str):
                            profile_data['core_values'] = json.loads(profile_data['core_values'])
                        elif not isinstance(profile_data['core_values'], list):
                            profile_data['core_values'] = []
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"Invalid core_values JSON for org {org_id}, setting to empty list")
                        profile_data['core_values'] = []
                else:
                    profile_data['core_values'] = []
                
                logger.info(f"Successfully fetched organization profile for org {org_id}")
                return {'data': profile_data}
            else:
                # Return default structure if no profile exists
                logger.info(f"No profile found for org {org_id}, returning default structure")
                return {
                    'data': {
                        'org_id': org_id,
                        'vision': None,
                        'mission': None,
                        'core_values': [],
                        'company_culture': None,
                        'founding_year': None,
                        'industry': None,
                        'company_size': None,
                        'headquarters': None,
                        'website_url': None,
                        'sustainability_goals': None,
                        'diversity_commitment': None,
                        'community_involvement': None,
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error fetching organization profile for org {org_id}: {str(e)}")
            raise Exception(f"Failed to fetch organization profile: {str(e)}")

    @staticmethod
    async def create_or_update_profile(
        org_id: str,
        profile_data: OrganizationProfileCreate,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Create or update organization profile.
        
        Args:
            org_id: Organization ID
            profile_data: Profile data to save
            user_id: User ID making the change
            
        Returns:
            Dict containing operation result
        """
        supabase = get_supabase_client()
        
        try:
            # Check if profile exists
            existing = await OrganizationProfileService.get_organization_profile(org_id)
            
            # Prepare data for database
            db_data = profile_data.dict(exclude_unset=True)
            
            # Process core values
            if 'core_values' in db_data:
                # Add IDs and timestamps to core values if missing
                processed_values = []
                for i, value in enumerate(db_data['core_values']):
                    if isinstance(value, dict):
                        # Ensure each value has an ID
                        if not value.get('id'):
                            value['id'] = str(uuid.uuid4())
                        # Ensure created_at timestamp
                        if not value.get('created_at'):
                            value['created_at'] = datetime.utcnow().isoformat()
                        # Set order based on position
                        value['order'] = i + 1
                        processed_values.append(value)
                
                # Store as JSON
                db_data['core_values'] = json.dumps(processed_values)
            
            # Convert None values to empty strings for database compatibility
            for key, value in db_data.items():
                if value is None and key not in ['founding_year', 'core_values']:
                    db_data[key] = ''
            
            if existing['data'].get('id'):
                # Update existing profile
                db_data['last_updated_by'] = user_id
                
                def update_op():
                    return supabase.from_("organization_profile").update(db_data).eq(
                        'org_id', org_id
                    ).execute()
                
                result = await safe_supabase_operation(update_op, "Failed to update organization profile")
                logger.info(f"Successfully updated organization profile for org {org_id}")
                
            else:
                # Create new profile
                db_data.update({
                    'org_id': org_id,
                    'created_by': user_id,
                    'last_updated_by': user_id
                })
                
                def create_op():
                    return supabase.from_("organization_profile").insert(db_data).execute()
                
                result = await safe_supabase_operation(create_op, "Failed to create organization profile")
                logger.info(f"Successfully created organization profile for org {org_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error saving organization profile for org {org_id}: {str(e)}")
            raise Exception(f"Failed to save organization profile: {str(e)}")

    @staticmethod
    async def delete_organization_profile(org_id: str, user_id: str) -> Dict[str, Any]:
        """
        Delete organization profile.
        
        Args:
            org_id: Organization ID
            user_id: User ID making the deletion
            
        Returns:
            Dict containing operation result
        """
        supabase = get_supabase_client()
        
        try:
            def delete_op():
                return supabase.from_("organization_profile").delete().eq(
                    "org_id", org_id
                ).execute()
            
            result = await safe_supabase_operation(delete_op, "Failed to delete organization profile")
            
            logger.info(f"Successfully deleted organization profile for org {org_id} by user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error deleting organization profile for org {org_id}: {str(e)}")
            raise Exception(f"Failed to delete organization profile: {str(e)}")

    @staticmethod
    def _process_core_values(core_values: list) -> list:
        """
        Process and validate core values list.
        
        Args:
            core_values: List of core value dictionaries
            
        Returns:
            Processed list of core values
        """
        if not core_values or not isinstance(core_values, list):
            return []
        
        processed = []
        for i, value in enumerate(core_values):
            if not isinstance(value, dict):
                continue
            
            # Validate required fields
            if not value.get('title') or not value.get('description'):
                continue
            
            # Process the value
            processed_value = {
                'id': value.get('id') or str(uuid.uuid4()),
                'title': str(value.get('title', '')).strip()[:100],
                'description': str(value.get('description', '')).strip()[:500],
                'icon': str(value.get('icon', 'star')).strip()[:50] or 'star',
                'order': i + 1,
                'created_at': value.get('created_at') or datetime.utcnow().isoformat()
            }
            
            processed.append(processed_value)
        
        return processed[:10]  # Limit to 10 values


# Convenience functions for backward compatibility
async def get_organization_profile(org_id: str) -> Dict[str, Any]:
    """Wrapper function for the service method"""
    return await OrganizationProfileService.get_organization_profile(org_id)

async def create_or_update_organization_profile(
    org_id: str, 
    profile_data: OrganizationProfileCreate, 
    user_id: str
) -> Dict[str, Any]:
    """Wrapper function for the service method"""
    return await OrganizationProfileService.create_or_update_profile(org_id, profile_data, user_id)

async def delete_organization_profile(org_id: str, user_id: str) -> Dict[str, Any]:
    """Wrapper function for the service method"""
    return await OrganizationProfileService.delete_organization_profile(org_id, user_id)
