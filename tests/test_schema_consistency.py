import pytest
from models.enums import (
    RoleEnum, ProjectStatusEnum, TaskStatusEnum, 
    PriorityEnum, DesignationEnum, InviteStatusEnum
)

class TestSchemaConsistency:
    """Test that our enums and models are consistent with the database schema"""
    
    def test_role_enum_matches_schema(self):
        """Test that RoleEnum values match the schema definition"""
        # From Enums.txt: role values are 'owner', 'member'
        expected_values = {'owner', 'member'}
        actual_values = {enum.value for enum in RoleEnum}
        assert actual_values == expected_values
    
    def test_project_status_enum_matches_schema(self):
        """Test that ProjectStatusEnum values match the schema definition"""
        # From Enums.txt: project_status values
        expected_values = {
            'planning', 'in_progress', 'not_started', 
            'completed', 'archived', 'on_hold'
        }
        actual_values = {enum.value for enum in ProjectStatusEnum}
        assert actual_values == expected_values
    
    def test_task_status_enum_matches_schema(self):
        """Test that TaskStatusEnum values match the schema definition"""
        # From Enums.txt: task_status values
        expected_values = {
            'not_started', 'in_progress', 'blocked', 
            'completed', 'archived', 'on_hold'
        }
        actual_values = {enum.value for enum in TaskStatusEnum}
        assert actual_values == expected_values
    
    def test_priority_enum_matches_schema(self):
        """Test that PriorityEnum values match the schema definition"""
        # From Enums.txt: priority values
        expected_values = {'high', 'medium', 'low', 'none', 'critical'}
        actual_values = {enum.value for enum in PriorityEnum}
        assert actual_values == expected_values
    
    def test_designation_enum_matches_schema(self):
        """Test that DesignationEnum values match the schema definition"""
        # From Enums.txt: designations values
        expected_values = {
            'developer', 'designer', 'qa', 'product_manager', 
            'devops_engineer', 'devops', 'analyst', 'team_lead', 
            'tester', 'director', 'manager', 'ui_engineer'
        }
        actual_values = {enum.value for enum in DesignationEnum}
        assert actual_values == expected_values
    
    def test_invite_status_enum_matches_schema(self):
        """Test that InviteStatusEnum values match the schema definition"""
        # From Enums.txt: invite_status values
        expected_values = {'pending', 'expired', 'cancelled', 'accepted'}
        actual_values = {enum.value for enum in InviteStatusEnum}
        assert actual_values == expected_values
    
    def test_enum_string_representation(self):
        """Test that enum values are properly stringified"""
        assert RoleEnum.OWNER.value == "owner"
        assert ProjectStatusEnum.IN_PROGRESS.value == "in_progress"
        assert TaskStatusEnum.BLOCKED.value == "blocked"
        assert PriorityEnum.CRITICAL.value == "critical"
        assert DesignationEnum.PRODUCT_MANAGER.value == "product_manager"
        assert InviteStatusEnum.PENDING.value == "pending"
    
    def test_enum_json_serialization(self):
        """Test that enum values can be JSON serialized"""
        import json
        
        # Test that enums can be serialized to JSON
        data = {
            "role": RoleEnum.OWNER,
            "status": ProjectStatusEnum.IN_PROGRESS,
            "priority": PriorityEnum.HIGH
        }
        
        json_str = json.dumps(data, default=str)
        assert "owner" in json_str
        assert "in_progress" in json_str
        assert "high" in json_str 