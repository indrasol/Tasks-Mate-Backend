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

def test_create_task_success(valid_token):
    payload = {"title": "task", "description": "desc"}
    response = client.post("/tasks/", json=payload, headers={"Authorization": valid_token})
    assert response.status_code in (200, 201)

def test_create_task_invalid_token(invalid_token):
    payload = {"title": "task2", "description": "desc2"}
    response = client.post("/tasks/", json=payload, headers={"Authorization": invalid_token})
    assert response.status_code == 401

def test_read_task_not_found(valid_token):
    response = client.get("/tasks/invalid-id", headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_update_task_unauthorized(valid_token):
    payload = {"title": "task", "description": "desc"}
    response = client.put("/tasks/invalid-id", json=payload, headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_delete_task_unauthorized(valid_token):
    response = client.delete("/tasks/invalid-id", headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_tasks_pagination(owner_token):
    response = client.get("/tasks/?limit=2&offset=0", headers={"Authorization": owner_token})
    assert response.status_code == 200
    assert len(response.json()) <= 2

def test_tasks_search(owner_token):
    response = client.get("/tasks/?search=bug", headers={"Authorization": owner_token})
    assert response.status_code == 200
    for task in response.json():
        assert "bug" in task["title"].lower()

def test_tasks_sorting(owner_token):
    response = client.get("/tasks/?sort_by=title&sort_order=desc", headers={"Authorization": owner_token})
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == sorted(titles, reverse=True)

def test_tasks_filter_status(owner_token):
    response = client.get("/tasks/?status=completed", headers={"Authorization": owner_token})
    assert response.status_code == 200
    for task in response.json():
        assert task["status"] == "completed"

def test_tasks_project_access_denied(outsider_token):
    response = client.get("/tasks/?project_id=proj1", headers={"Authorization": outsider_token})
    assert response.status_code == 403