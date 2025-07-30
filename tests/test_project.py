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

def test_create_project_success(valid_token):
    payload = {"name": "proj", "description": "desc"}
    response = client.post("/projects/", json=payload, headers={"Authorization": valid_token})
    assert response.status_code in (200, 201)

def test_create_project_invalid_token(invalid_token):
    payload = {"name": "proj2", "description": "desc2"}
    response = client.post("/projects/", json=payload, headers={"Authorization": invalid_token})
    assert response.status_code == 401

def test_read_project_not_found(valid_token):
    response = client.get("/projects/invalid-id", headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_update_project_unauthorized(valid_token):
    payload = {"name": "proj", "description": "desc"}
    response = client.put("/projects/invalid-id", json=payload, headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_delete_project_unauthorized(valid_token):
    response = client.delete("/projects/invalid-id", headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)