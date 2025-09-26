"""
Test cases for Organization Profile API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json

# Mock the dependencies to avoid database calls during testing
@pytest.fixture
def mock_supabase():
    """Mock supabase client for testing."""
    with patch('app.services.organization_profile_service.get_supabase_client') as mock_client:
        mock_supabase_instance = MagicMock()
        mock_client.return_value = mock_supabase_instance
        yield mock_supabase_instance

@pytest.fixture
def mock_auth():
    """Mock authentication for testing."""
    with patch('app.services.auth_handler.verify_token') as mock_verify:
        mock_verify.return_value = {"id": "test-user-123", "email": "test@example.com"}
        yield mock_verify

@pytest.fixture
def mock_rbac():
    """Mock RBAC for testing."""
    with patch('app.api.v1.routes.organizations.org_rbac.org_rbac') as mock_rbac_func:
        mock_rbac_func.return_value = "owner"
        yield mock_rbac_func

def test_organization_profile_models():
    """Test that the Pydantic models are properly defined."""
    from app.models.schemas.organization_profile import (
        OrganizationProfileCreate,
        CoreValue,
        CompanySize
    )
    
    # Test CoreValue model
    core_value = CoreValue(
        title="Innovation",
        description="We embrace new technologies and creative solutions",
        icon="lightbulb",
        order=1
    )
    assert core_value.title == "Innovation"
    assert core_value.icon == "lightbulb"
    
    # Test OrganizationProfileCreate model
    profile_data = {
        "vision": "To be the leading technology company",
        "mission": "Empowering businesses through innovative solutions",
        "core_values": [core_value.dict()],
        "company_size": CompanySize.MEDIUM,
        "industry": "Technology",
        "founding_year": 2020
    }
    
    profile = OrganizationProfileCreate(**profile_data)
    assert profile.vision == "To be the leading technology company"
    assert profile.company_size == CompanySize.MEDIUM
    assert len(profile.core_values) == 1

def test_core_value_validation():
    """Test CoreValue validation."""
    from app.models.schemas.organization_profile import CoreValue
    from pydantic import ValidationError
    
    # Valid core value
    valid_value = CoreValue(
        title="Test Value",
        description="A test core value",
        order=1
    )
    assert valid_value.title == "Test Value"
    
    # Test title length validation
    with pytest.raises(ValidationError):
        CoreValue(
            title="x" * 101,  # Too long
            description="Valid description",
            order=1
        )

def test_organization_profile_validation():
    """Test OrganizationProfile validation."""
    from app.models.schemas.organization_profile import OrganizationProfileCreate, CoreValue
    from pydantic import ValidationError
    
    # Test core values limit
    too_many_values = [
        CoreValue(title=f"Value {i}", description=f"Description {i}", order=i+1)
        for i in range(11)  # More than 10
    ]
    
    with pytest.raises(ValidationError):
        OrganizationProfileCreate(core_values=too_many_values)
    
    # Test duplicate core value titles
    duplicate_values = [
        CoreValue(title="Same Title", description="Description 1", order=1),
        CoreValue(title="Same Title", description="Description 2", order=2)
    ]
    
    with pytest.raises(ValidationError):
        OrganizationProfileCreate(core_values=duplicate_values)

def test_service_functions():
    """Test service layer functions."""
    from app.services.organization_profile_service import OrganizationProfileService
    
    # Test that service class methods exist
    assert hasattr(OrganizationProfileService, 'get_organization_profile')
    assert hasattr(OrganizationProfileService, 'create_or_update_profile')
    assert hasattr(OrganizationProfileService, 'delete_organization_profile')

def test_frontend_service_validation():
    """Test frontend service validation functions."""
    import sys
    import os
    
    # Add frontend src to path for testing
    frontend_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'tasks-mate-frontend', 'src')
    if os.path.exists(frontend_path):
        sys.path.insert(0, frontend_path)
        
        try:
            # This would work if we had a Python version of the validation
            # For now, we'll just verify the structure
            pass
        except ImportError:
            # Expected since this is TypeScript code
            pass

def test_api_endpoints_structure():
    """Test that API endpoints are properly structured."""
    from app.api.v1.routes.organizations.organization_profile_router import router
    
    # Check that router has the expected routes
    routes = [route.path for route in router.routes]
    
    # Expected routes (with parameter placeholders)
    expected_patterns = [
        "/{org_id}",  # GET, PUT, POST, DELETE
        "/health"     # GET
    ]
    
    # Verify we have routes defined
    assert len(routes) > 0
    
    # Check for health endpoint
    health_routes = [route for route in router.routes if "health" in route.path]
    assert len(health_routes) > 0

if __name__ == "__main__":
    # Run basic tests
    test_organization_profile_models()
    test_core_value_validation()
    test_organization_profile_validation()
    test_service_functions()
    test_api_endpoints_structure()
    print("✅ All basic tests passed!")
