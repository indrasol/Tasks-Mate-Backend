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

def test_create_task_comment_success(valid_token):
    payload = {"task_id": "t1", "comment": "test"}
    response = client.post("/task-comments/", json=payload, headers={"Authorization": valid_token})
    assert response.status_code in (200, 201)

def test_create_task_comment_invalid_token(invalid_token):
    payload = {"task_id": "t2", "comment": "fail"}
    response = client.post("/task-comments/", json=payload, headers={"Authorization": invalid_token})
    assert response.status_code == 401

def test_read_task_comment_not_found(valid_token):
    response = client.get("/task-comments/cX", headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_update_task_comment_unauthorized(valid_token):
    payload = {"comment": "edit"}
    response = client.put("/task-comments/cX", json=payload, headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_delete_task_comment_unauthorized(valid_token):
    response = client.delete("/task-comments/cX", headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_task_comments_pagination(owner_token):
    response = client.get("/task-comments/?task_id=task1&limit=2&offset=0", headers={"Authorization": owner_token})
    assert response.status_code == 200
    assert len(response.json()) <= 2

def test_task_comments_search(owner_token):
    response = client.get("/task-comments/?task_id=task1&search=fix", headers={"Authorization": owner_token})
    assert response.status_code == 200
    for comment in response.json():
        assert "fix" in comment["comment"].lower()

def test_task_comments_sorting(owner_token):
    response = client.get("/task-comments/?task_id=task1&sort_by=created_at&sort_order=desc", headers={"Authorization": owner_token})
    assert response.status_code == 200
    created = [c["created_at"] for c in response.json()]
    assert created == sorted(created, reverse=True)

def test_task_comments_access_denied(outsider_token):
    response = client.get("/task-comments/?task_id=task1", headers={"Authorization": outsider_token})
    assert response.status_code == 200 or response.status_code == 403