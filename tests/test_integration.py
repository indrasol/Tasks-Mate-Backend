import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def valid_token():
    return "Bearer validtoken"

@pytest.fixture
def another_token():
    return "Bearer anothertoken"

@pytest.fixture
def setup_org_and_user(valid_token):
    user_payload = {"user_id": "u300", "tenant_name": "org300", "email": "u300@x.com", "username": "user300"}
    client.post("/register", json=user_payload, headers={"Authorization": valid_token})
    org_payload = {"name": "org300", "description": "desc"}
    r = client.post("/organizations/", json=org_payload, headers={"Authorization": valid_token})
    org_id = r.json().get("org_id") or "org300"
    yield {"user_id": "u300", "org_id": org_id}
    client.delete(f"/organizations/{org_id}", headers={"Authorization": valid_token})

def test_permission_denied(another_token):
    r = client.get("/projects/unknown", headers={"Authorization": another_token})
    assert r.status_code in (403, 404)

def test_duplicate_org(valid_token):
    org_payload = {"name": "orgdup", "description": "desc"}
    r1 = client.post("/organizations/", json=org_payload, headers={"Authorization": valid_token})
    r2 = client.post("/organizations/", json=org_payload, headers={"Authorization": valid_token})
    assert r1.status_code in (200, 201)
    assert r2.status_code in (400, 409)
    org_id = r1.json().get("org_id") or "orgdup"
    client.delete(f"/organizations/{org_id}", headers={"Authorization": valid_token})

def test_cascade_delete(valid_token):
    org_payload = {"name": "orgdel", "description": "desc"}
    r = client.post("/organizations/", json=org_payload, headers={"Authorization": valid_token})
    org_id = r.json().get("org_id") or "orgdel"
    project_payload = {"name": "projdel", "description": "desc"}
    r = client.post("/projects/", json=project_payload, headers={"Authorization": valid_token})
    project_id = r.json().get("project_id") or "projdel"
    client.delete(f"/organizations/{org_id}", headers={"Authorization": valid_token})
    r = client.get(f"/projects/{project_id}", headers={"Authorization": valid_token})
    assert r.status_code in (403, 404)

def test_invite_accept_flow(valid_token, another_token):
    org_payload = {"name": "orginvite", "description": "desc"}
    r = client.post("/organizations/", json=org_payload, headers={"Authorization": valid_token})
    org_id = r.json().get("org_id") or "orginvite"
    invite_payload = {"org_id": org_id, "email": "invitee@x.com"}
    r = client.post("/organization-invites/", json=invite_payload, headers={"Authorization": valid_token})
    invite_id = r.json().get("invite_id") or "inv1"
    r = client.put(f"/organization-invites/{invite_id}/accept?org_id={org_id}", headers={"Authorization": another_token})
    assert r.status_code in (200, 201)
    client.delete(f"/organizations/{org_id}", headers={"Authorization": valid_token})

def test_full_flow_with_cleanup(valid_token):
    user_payload = {"user_id": "u400", "tenant_name": "org400", "email": "u400@x.com", "username": "user400"}
    client.post("/register", json=user_payload, headers={"Authorization": valid_token})
    org_payload = {"name": "org400", "description": "desc"}
    r = client.post("/organizations/", json=org_payload, headers={"Authorization": valid_token})
    org_id = r.json().get("org_id") or "org400"
    member_payload = {"user_id": "u400", "org_id": org_id, "role": "member"}
    client.post("/organization-members/", json=member_payload, headers={"Authorization": valid_token})
    project_payload = {"name": "proj400", "description": "desc"}
    r = client.post("/projects/", json=project_payload, headers={"Authorization": valid_token})
    project_id = r.json().get("project_id") or "proj400"
    proj_member_payload = {"user_id": "u400", "project_id": project_id, "role": "member"}
    client.post("/project-members/", json=proj_member_payload, headers={"Authorization": valid_token})
    task_payload = {"title": "task400", "description": "desc", "project_id": project_id}
    r = client.post("/tasks/", json=task_payload, headers={"Authorization": valid_token})
    task_id = r.json().get("task_id") or "task400"
    comment_payload = {"task_id": task_id, "comment": "Looks good"}
    client.post("/task-comments/", json=comment_payload, headers={"Authorization": valid_token})
    r = client.get("/task-history/", headers={"Authorization": valid_token})
    assert r.status_code in (200, 201, 204)
    client.delete(f"/projects/{project_id}", headers={"Authorization": valid_token})
    client.delete(f"/organizations/{org_id}", headers={"Authorization": valid_token})