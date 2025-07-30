import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def valid_token():
    return "Bearer validtoken"

@pytest.fixture
def invalid_token():
    return "Bearer invalid"

def test_create_member_success(valid_token):
    payload = {"user_id": "u1", "org_id": "o1", "role": "member"}
    response = client.post("/organization-members/", json=payload, headers={"Authorization": valid_token})
    assert response.status_code in (200, 201)

def test_create_member_invalid_token(invalid_token):
    payload = {"user_id": "u2", "org_id": "o2", "role": "member"}
    response = client.post("/organization-members/", json=payload, headers={"Authorization": invalid_token})
    assert response.status_code == 401

def test_read_member_not_found(valid_token):
    response = client.get("/organization-members/uX/oX", headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_update_member_unauthorized(valid_token):
    payload = {"role": "admin"}
    response = client.put("/organization-members/uX/oX", json=payload, headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_delete_member_unauthorized(valid_token):
    response = client.delete("/organization-members/uX/oX", headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)