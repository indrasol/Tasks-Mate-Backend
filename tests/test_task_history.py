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

def test_get_task_history_success(valid_token):
    response = client.get("/task-history/", headers={"Authorization": valid_token})
    assert response.status_code in (200, 201, 204)

def test_get_task_history_invalid_token(invalid_token):
    response = client.get("/task-history/", headers={"Authorization": invalid_token})
    assert response.status_code == 401