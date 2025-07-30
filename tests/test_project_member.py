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

def test_project_members_pagination(owner_token):
    response = client.get("/project-members/?project_id=proj1&limit=2&offset=0", headers={"Authorization": owner_token})
    assert response.status_code == 200
    assert len(response.json()) <= 2

def test_project_members_search(owner_token):
    response = client.get("/project-members/?project_id=proj1&search=alice", headers={"Authorization": owner_token})
    assert response.status_code == 200
    for member in response.json():
        assert "alice" in member["user_name"].lower()

def test_project_members_sorting(owner_token):
    response = client.get("/project-members/?project_id=proj1&sort_by=user_name&sort_order=desc", headers={"Authorization": owner_token})
    assert response.status_code == 200
    names = [m["user_name"] for m in response.json()]
    assert names == sorted(names, reverse=True)

def test_project_members_filter_role(owner_token):
    response = client.get("/project-members/?project_id=proj1&role=admin", headers={"Authorization": owner_token})
    assert response.status_code == 200
    for member in response.json():
        assert member["role"] == "admin"

def test_project_members_access_denied(outsider_token):
    response = client.get("/project-members/?project_id=proj1", headers={"Authorization": outsider_token})
    assert response.status_code == 403