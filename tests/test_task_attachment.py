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

def test_create_task_attachment_success(valid_token):
    payload = {"task_id": "t1", "file_url": "url"}
    response = client.post("/task-attachments/", json=payload, headers={"Authorization": valid_token})
    assert response.status_code in (200, 201)

def test_create_task_attachment_invalid_token(invalid_token):
    payload = {"task_id": "t2", "file_url": "url2"}
    response = client.post("/task-attachments/", json=payload, headers={"Authorization": invalid_token})
    assert response.status_code == 401

def test_read_task_attachment_not_found(valid_token):
    response = client.get("/task-attachments/aX", headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_update_task_attachment_unauthorized(valid_token):
    payload = {"file_url": "url3"}
    response = client.put("/task-attachments/aX", json=payload, headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)

def test_delete_task_attachment_unauthorized(valid_token):
    response = client.delete("/task-attachments/aX", headers={"Authorization": valid_token})
    assert response.status_code in (403, 404)