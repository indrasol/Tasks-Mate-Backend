import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def owner_token():
    return "Bearer owner_token"

@pytest.fixture
def member_token():
    return "Bearer member_token"

@pytest.fixture
def outsider_token():
    return "Bearer outsider_token"

def test_create_project_resource_success(valid_token):
    payload = {"project_id": "p1", "resource_type": "doc", "resource_url": "url"}
    response = client.post("/project-resources/", json=payload, headers={"Authorization": valid_token})
    assert response.status_code in (200, 201)

def test_create_project_resource_invalid_token(invalid_token):
    payload = {"project_id": "p2", "resource_type": "img", "resource_url": "url2"}
    response = client.post("/project-resources/", json=payload, headers={"Authorization": invalid_token})
    assert response.status_code == 401

def test_read_project_resource_not_found(valid_token):
    response = client.get("/project-resources/rX", headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_update_project_resource_unauthorized(valid_token):
    payload = {"resource_type": "pdf"}
    response = client.put("/project-resources/rX", json=payload, headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_delete_project_resource_unauthorized(valid_token):
    response = client.delete("/project-resources/rX", headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_project_resources_pagination(owner_token):
    response = client.get("/project-resources/?project_id=proj1&limit=2&offset=0", headers={"Authorization": owner_token})
    assert response.status_code == 200
    assert len(response.json()) <= 2

def test_project_resources_search(owner_token):
    response = client.get("/project-resources/?project_id=proj1&search=doc", headers={"Authorization": owner_token})
    assert response.status_code == 200
    for res in response.json():
        assert "doc" in res["resource_type"].lower()

def test_project_resources_sorting(owner_token):
    response = client.get("/project-resources/?project_id=proj1&sort_by=resource_type&sort_order=desc", headers={"Authorization": owner_token})
    assert response.status_code == 200
    types = [r["resource_type"] for r in response.json()]
    assert types == sorted(types, reverse=True)

def test_project_resources_filter_type(owner_token):
    response = client.get("/project-resources/?project_id=proj1&resource_type=doc", headers={"Authorization": owner_token})
    assert response.status_code == 200
    for res in response.json():
        assert res["resource_type"] == "doc"

def test_project_resources_access_denied(outsider_token):
    response = client.get("/project-resources/?project_id=proj1", headers={"Authorization": outsider_token})
    assert response.status_code == 403