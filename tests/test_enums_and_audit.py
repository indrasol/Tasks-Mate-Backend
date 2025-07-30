import pytest
from models.enums import (
    RoleEnum, ProjectStatusEnum, TaskStatusEnum, 
    PriorityEnum, DesignationEnum, InviteStatusEnum
)
from services.utils import inject_audit_fields
from uuid import uuid4

class TestEnums:
    """Test enum functionality and validation"""
    
    def test_role_enum_values(self):
        """Test RoleEnum has correct values"""
        assert RoleEnum.OWNER == "owner"
        assert RoleEnum.MEMBER == "member"
        assert len(RoleEnum) == 2
    
    def test_project_status_enum_values(self):
        """Test ProjectStatusEnum has correct values"""
        assert ProjectStatusEnum.PLANNING == "planning"
        assert ProjectStatusEnum.IN_PROGRESS == "in_progress"
        assert ProjectStatusEnum.NOT_STARTED == "not_started"
        assert ProjectStatusEnum.COMPLETED == "completed"
        assert ProjectStatusEnum.ARCHIVED == "archived"
        assert ProjectStatusEnum.ON_HOLD == "on_hold"
        assert len(ProjectStatusEnum) == 6
    
    def test_task_status_enum_values(self):
        """Test TaskStatusEnum has correct values"""
        assert TaskStatusEnum.NOT_STARTED == "not_started"
        assert TaskStatusEnum.IN_PROGRESS == "in_progress"
        assert TaskStatusEnum.BLOCKED == "blocked"
        assert TaskStatusEnum.COMPLETED == "completed"
        assert TaskStatusEnum.ARCHIVED == "archived"
        assert TaskStatusEnum.ON_HOLD == "on_hold"
        assert len(TaskStatusEnum) == 6
    
    def test_priority_enum_values(self):
        """Test PriorityEnum has correct values"""
        assert PriorityEnum.HIGH == "high"
        assert PriorityEnum.MEDIUM == "medium"
        assert PriorityEnum.LOW == "low"
        assert PriorityEnum.NONE == "none"
        assert PriorityEnum.CRITICAL == "critical"
        assert len(PriorityEnum) == 5
    
    def test_designation_enum_values(self):
        """Test DesignationEnum has correct values"""
        assert DesignationEnum.DEVELOPER == "developer"
        assert DesignationEnum.DESIGNER == "designer"
        assert DesignationEnum.QA == "qa"
        assert DesignationEnum.PRODUCT_MANAGER == "product_manager"
        assert DesignationEnum.DEVOPS_ENGINEER == "devops_engineer"
        assert DesignationEnum.DEVOPS == "devops"
        assert DesignationEnum.ANALYST == "analyst"
        assert DesignationEnum.TEAM_LEAD == "team_lead"
        assert DesignationEnum.TESTER == "tester"
        assert DesignationEnum.DIRECTOR == "director"
        assert DesignationEnum.MANAGER == "manager"
        assert DesignationEnum.UI_ENGINEER == "ui_engineer"
        assert len(DesignationEnum) == 12
    
    def test_invite_status_enum_values(self):
        """Test InviteStatusEnum has correct values"""
        assert InviteStatusEnum.PENDING == "pending"
        assert InviteStatusEnum.EXPIRED == "expired"
        assert InviteStatusEnum.CANCELLED == "cancelled"
        assert InviteStatusEnum.ACCEPTED == "accepted"
        assert len(InviteStatusEnum) == 4

class TestAuditFields:
    """Test audit field injection functionality"""
    
    def test_inject_audit_fields_create(self):
        """Test audit field injection for create action"""
        user_id = str(uuid4())
        data = {"name": "Test Project", "description": "Test Description"}
        
        result = inject_audit_fields(data, user_id, "create")
        
        assert result["created_by"] == user_id
        assert "created_at" in result
        assert result["name"] == "Test Project"
        assert result["description"] == "Test Description"
    
    def test_inject_audit_fields_update(self):
        """Test audit field injection for update action"""
        user_id = str(uuid4())
        data = {"name": "Updated Project", "description": "Updated Description"}
        
        result = inject_audit_fields(data, user_id, "update")
        
        assert result["updated_by"] == user_id
        assert "updated_at" in result
        assert result["name"] == "Updated Project"
        assert result["description"] == "Updated Description"
    
    def test_inject_audit_fields_delete(self):
        """Test audit field injection for delete action"""
        user_id = str(uuid4())
        data = {"is_deleted": True, "delete_reason": "Test deletion"}
        
        result = inject_audit_fields(data, user_id, "delete")
        
        assert result["deleted_by"] == user_id
        assert "deleted_at" in result
        assert result["is_deleted"] == True
        assert result["delete_reason"] == "Test deletion"
    
    def test_inject_audit_fields_accept(self):
        """Test audit field injection for accept action"""
        user_id = str(uuid4())
        data = {"invite_status": "accepted"}
        
        result = inject_audit_fields(data, user_id, "accept")
        
        assert result["accepted_by"] == user_id
        assert "accepted_at" in result
        assert result["invite_status"] == "accepted"
    
    def test_inject_audit_fields_with_extra(self):
        """Test audit field injection with extra fields"""
        user_id = str(uuid4())
        data = {"name": "Test"}
        extra = {"custom_field": "custom_value"}
        
        result = inject_audit_fields(data, user_id, "create", extra)
        
        assert result["created_by"] == user_id
        assert result["custom_field"] == "custom_value"
        assert result["name"] == "Test"
    
    def test_inject_audit_fields_preserves_existing(self):
        """Test that existing audit fields are preserved"""
        user_id = str(uuid4())
        existing_created_by = str(uuid4())
        data = {
            "name": "Test",
            "created_by": existing_created_by,
            "created_at": "2024-01-01T00:00:00"
        }
        
        result = inject_audit_fields(data, user_id, "update")
        
        # Should preserve existing created_by and created_at
        assert result["created_by"] == existing_created_by
        assert result["created_at"] == "2024-01-01T00:00:00"
        # Should add new updated_by and updated_at
        assert result["updated_by"] == user_id
        assert "updated_at" in result 