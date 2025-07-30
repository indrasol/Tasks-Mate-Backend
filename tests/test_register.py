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

def test_register_success(valid_token):
    payload = {"user_id": "u1", "tenant_name": "org", "email": "a@b.com", "username": "user"}
    response = client.post("/register", json=payload, headers={"Authorization": valid_token})
    assert response.status_code in (200, 201)

def test_register_missing_field(valid_token):
    payload = {"user_id": "u2", "tenant_name": "org", "username": "user2"}
    response = client.post("/register", json=payload, headers={"Authorization": valid_token})
    assert response.status_code == 422

def test_register_invalid_token(invalid_token):
    payload = {"user_id": "u3", "tenant_name": "org", "email": "b@c.com", "username": "user3"}
    response = client.post("/register", json=payload, headers={"Authorization": invalid_token})
    assert response.status_code == 401

def test_register_pending_success(valid_token):
    payload = {"user_id": "u4", "tenant_name": "org", "email": "c@d.com", "username": "user4"}
    response = client.post("/register/pending", json=payload, headers={"X-API-Key": "testkey"})
    assert response.status_code in (200, 201)

def test_authenticate_success(valid_token):
    response = client.get("/authenticate", headers={"Authorization": valid_token})
    assert response.status_code == 200

def test_authenticate_invalid_token(invalid_token):
    response = client.get("/authenticate", headers={"Authorization": invalid_token})
    assert response.status_code == 401

def test_login_success(valid_token):
    payload = {"identifier": "user"}
    response = client.post("/login", json=payload, headers={"Authorization": valid_token})
    assert response.status_code == 200

def test_login_invalid_token(invalid_token):
    payload = {"identifier": "user"}
    response = client.post("/login", json=payload, headers={"Authorization": invalid_token})
    assert response.status_code == 401

def test_get_email_success():
    payload = {"username": "user"}
    response = client.post("/get-email", json=payload, headers={"X-API-Key": "testkey"})
    assert response.status_code == 200