import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/")
    assert response.status_code == 200
    # Optionally check response content if root returns JSON or text
    # assert response.json() == {"message": "..."}