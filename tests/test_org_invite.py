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

def test_create_invite_success(valid_token):
    payload = {"org_id": "o1", "email": "a@b.com"}
    response = client.post("/organization-invites/", json=payload, headers={"Authorization": valid_token})
    assert response.status_code in (200, 201)

def test_create_invite_invalid_token(invalid_token):
    payload = {"org_id": "o2", "email": "b@c.com"}
    response = client.post("/organization-invites/", json=payload, headers={"Authorization": invalid_token})
    assert response.status_code == 401

def test_read_invite_not_found(valid_token):
    response = client.get("/organization-invites/invX?org_id=oX", headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_update_invite_unauthorized(valid_token):
    payload = {"email": "c@d.com"}
    response = client.put("/organization-invites/invX?org_id=oX", json=payload, headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_accept_invite_unauthorized(valid_token):
    response = client.put("/organization-invites/invX/accept?org_id=oX", headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_delete_invite_unauthorized(valid_token):
    response = client.delete("/organization-invites/invX?org_id=oX", headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)