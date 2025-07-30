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

@pytest.fixture
def invited_token():
    return "Bearer invitedtoken"

def test_create_org_success(valid_token):
    payload = {"name": "org", "description": "desc"}
    response = client.post("/organizations/", json=payload, headers={"Authorization": valid_token})
    assert response.status_code in (200, 201)

def test_create_org_invalid_token(invalid_token):
    payload = {"name": "org2", "description": "desc2"}
    response = client.post("/organizations/", json=payload, headers={"Authorization": invalid_token})
    assert response.status_code == 401

def test_read_org_not_found(valid_token):
    response = client.get("/organizations/invalid-id", headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_update_org_unauthorized(valid_token):
    payload = {"name": "org", "description": "desc"}
    response = client.put("/organizations/invalid-id", json=payload, headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_delete_org_unauthorized(valid_token):
    response = client.delete("/organizations/invalid-id", headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_organizations_access_status_member(valid_token):
    response = client.get("/organizations/", headers={"Authorization": valid_token})
    assert response.status_code == 200
    for org in response.json():
        assert org["access_status"] == "member"

def test_organizations_access_status_invite(invited_token):
    response = client.get("/organizations/", headers={"Authorization": invited_token})
    assert response.status_code == 200
    for org in response.json():
        assert org["access_status"] == "invite"