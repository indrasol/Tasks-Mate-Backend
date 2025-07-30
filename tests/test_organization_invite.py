import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def owner_token():
    return "Bearer owner_token"

@pytest.fixture
def admin_token():
    return "Bearer admin_token"

@pytest.fixture
def outsider_token():
    return "Bearer outsider_token"

def test_org_invites_pagination(owner_token):
    response = client.get("/organization-invites/?org_id=org1&limit=2&offset=0", headers={"Authorization": owner_token})
    assert response.status_code == 200
    assert len(response.json()) <= 2

def test_org_invites_search(owner_token):
    response = client.get("/organization-invites/?org_id=org1&search=alice", headers={"Authorization": owner_token})
    assert response.status_code == 200
    for invite in response.json():
        assert "alice" in invite["email"].lower()

def test_org_invites_sorting(owner_token):
    response = client.get("/organization-invites/?org_id=org1&sort_by=email&sort_order=desc", headers={"Authorization": owner_token})
    assert response.status_code == 200
    emails = [i["email"] for i in response.json()]
    assert emails == sorted(emails, reverse=True)

def test_org_invites_filter_email(owner_token):
    response = client.get("/organization-invites/?org_id=org1&email=alice@example.com", headers={"Authorization": owner_token})
    assert response.status_code == 200
    for invite in response.json():
        assert invite["email"] == "alice@example.com"

def test_org_invites_access_denied(outsider_token):
    response = client.get("/organization-invites/?org_id=org1", headers={"Authorization": outsider_token})
    assert response.status_code == 403