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

def test_create_designation_success(valid_token):
    payload = {"org_id": "o1", "title": "Manager"}
    response = client.post("/designations/", json=payload, headers={"Authorization": valid_token})
    assert response.status_code in (200, 201)

def test_create_designation_invalid_token(invalid_token):
    payload = {"org_id": "o2", "title": "Lead"}
    response = client.post("/designations/", json=payload, headers={"Authorization": invalid_token})
    assert response.status_code == 401

def test_read_designation_not_found(valid_token):
    response = client.get("/designations/dX?org_id=oX", headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_update_designation_unauthorized(valid_token):
    payload = {"title": "Director"}
    response = client.put("/designations/dX?org_id=oX", json=payload, headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_delete_designation_unauthorized(valid_token):
    response = client.delete("/designations/dX?org_id=oX", headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)