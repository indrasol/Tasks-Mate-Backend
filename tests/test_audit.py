import pytest
from datetime import datetime
from services.utils import inject_audit_fields

def test_inject_audit_fields_create():
    data = {}
    user_id = "test-user"
    result = inject_audit_fields(data, user_id, "create")
    assert result["created_by"] == user_id
    assert "created_at" in result

def test_inject_audit_fields_update():
    data = {}
    user_id = "test-user"
    result = inject_audit_fields(data, user_id, "update")
    assert result["updated_by"] == user_id
    assert "updated_at" in result

def test_inject_audit_fields_delete():
    data = {}
    user_id = "test-user"
    result = inject_audit_fields(data, user_id, "delete")
    assert result["deleted_by"] == user_id
    assert "deleted_at" in result