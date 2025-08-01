
from models.enums import DesignationEnum, RoleEnum
import pytest
from fastapi.testclient import TestClient
from main import app
import jwt
import time
import os
import uuid
from dotenv import load_dotenv

from services.role_service import create_role, get_role_by_name

load_dotenv()

client = TestClient(app)
SUPABASE_SECRET_KEY = os.getenv("SUPABASESECRETKEYST")
assert SUPABASE_SECRET_KEY, "SUPABASE_SECRET_KEY is not set"
ALGORITHM = "HS256"

import logging

def pytest_configure(config):
    # Lower log verbosity for noisy modules
    logging.getLogger("hpack").setLevel(logging.WARNING)
    logging.getLogger("h2").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("supabase_py").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)  # if used
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.ERROR)


    logging.getLogger("hpack").disabled = True
    logging.getLogger("h2").disabled = True
    logging.getLogger("httpcore").disabled = True
    logging.getLogger("httpx").disabled = True


# -------- Utilities --------

def create_jwt_token(user_id: str, expire_seconds=3600):
    now = int(time.time())
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + expire_seconds,
        "aud": "authenticated"
    }
    token = jwt.encode(payload, SUPABASE_SECRET_KEY, algorithm=ALGORITHM)
    return f"Bearer {token}"


def generate_user(prefix="user"):
    if prefix == "existing":
        prefix = "creator"
        uid = "d5510c4d-80b7-4158-8255-58430905bee8" # "157901b5-df3f-487f-872d-bdeb4d3ba959"
    elif prefix == "existing_invited":
        prefix = "invited"
        uid = "157901b5-df3f-487f-872d-bdeb4d3ba959"
    else:       
        uid = str(uuid.uuid4())
    return {
        "user_id": uid,
        "username": f"{prefix}_{uid}",
        "email": f"{prefix}_{uid}@example.com"
    }


# -------- Fixtures --------

@pytest.fixture
def creator_user_fix():
    user = generate_user("creator")
    return {"user": user}


@pytest.fixture
def invited_user_fix():
    user = generate_user("invited")
    return {"user": user}

@pytest.fixture
def existing_user_fix():
    user = generate_user("existing")
    return {"user": user}

@pytest.fixture
def existing_invited_user_fix():
    user = generate_user("existing_invited")
    return {"user": user}

# -------- API Helpers --------

base_path = '/v1/routes'  # Add leading slash for safety

def api_post(path, data, token):
    url = base_path + path
    print(f"\n➡️ POST {url}\nPayload: {data}")
    r = client.post(url, json=data, headers={"Authorization": token})
    print(f"⬅️ Response [{r.status_code}]: {r.text}\n")
    return r


def api_get(path, token):
    url = base_path + path
    print(f"\n➡️ GET {url}")
    r = client.get(url, headers={"Authorization": token})
    print(f"⬅️ Response [{r.status_code}]: {r.text}\n")
    return r


def api_put(path, token):
    url = base_path + path
    print(f"\n➡️ PUT {url}")
    r = client.put(url, headers={"Authorization": token})
    print(f"⬅️ Response [{r.status_code}]: {r.text}\n")
    return r


def api_delete(path, token):
    url = base_path + path
    print(f"\n➡️ DELETE {url}")
    r = client.delete(url, headers={"Authorization": token})
    print(f"⬅️ Response [{r.status_code}]: {r.text}\n")
    return r


async def test_start_flow(creator_user_fix, invited_user_fix, existing_user_fix, existing_invited_user_fix):
   await full_user_org_flow(existing_user_fix, existing_invited_user_fix)
   # await full_user_org_flow(existing_invited_user_fix, None)
    # full_user_org_flow(existing_user_fix, invited_user_fix)
    # full_user_org_flow(creator_user_fix, invited_user_fix)
    # full_user_org_flow(invited_user_fix, {})  # invited_user has no invites at first


async def full_user_org_flow(creator_user, invited_user):
    creator = creator_user["user"]
    if isinstance(invited_user, dict) and "user" in invited_user:
        invited = invited_user["user"]
    else:
        invited = None
    token = create_jwt_token(creator["user_id"])
    print(f"\n🔑 Using token for user: {creator['username']}")

    # Register
    r = api_post("/register", creator, token)
    # assert r.status_code in (200, 201), f"Creator register failed: {r.text}"

    # Login
    r = api_post("/login", {"identifier": creator["username"]}, token)
    assert r.status_code in (200, 201), f"Login failed: {r.text}"
    assert r.json()["username"] == creator["username"]

    # Get organization invites
    r = api_get("/organization-invites/user", token)
    invites = r.json()
    if invites:
        invite = invites[0]
        print(f"📩 Invite object: {invite}")
        
        invite_id = invite.get("invite_id")
        org_id = invite.get("org_id")
        
        if not invite_id or not org_id:
            raise ValueError(f"Invalid invite data: {invite}")

        invite_id = str(invite_id)
        org_id = str(org_id)

        print(f"🔗 Accepting invite: {invite_id} for org: {org_id}")
        r = api_put(f"/organization-invites/{invite_id}/accept?org_id={org_id}", token)
        assert r.status_code in (200, 201), f"Accept invite failed: {r.text}"

    # Get or create organization
    r = api_get("/organizations/", token)
    if r.json():
        org_id = str(r.json()[0]["org_id"])
        print(f"🏢 Found existing org_id: {org_id}")
    else:
        org_name = "Org_" + uuid.uuid4().hex[:6]
        org_payload = {"name": org_name, "description": "Test Org"}
        r = api_post("/organizations/", org_payload, token)
        assert r.status_code in (200, 201), f"Create org failed: {r.text}"
        print(f"✅ Org created. Response: {r.json()}")
        org_id = str(r.json()["org_id"])
        print(f"🏢 Created org_id: {org_id}")

    # Get organization members
    r = api_get(f"/organization-members/?org_id={org_id}", token)
    members = r.json()

    print(f"{members}")

    if members:
        member_emails = [m.get("email") for m in members]
    else:
        member_emails = None

    result_role = await get_role_by_name(RoleEnum.MEMBER.value)
    if result_role.data and len(result_role.data) > 0:
        role_id = result_role.data[0]["role_id"]
    else:
        result_role = await create_role({"name":RoleEnum.MEMBER.value})
        if result_role.data:
            role_id = result_role.data[0]["role_id"]

    if invited and "email" in invited:        
        if invited["email"] not in member_emails:
            print(f"✉️ Inviting user: {invited['email']}")
            r = api_post("/organization-invites/", {"org_id": str(org_id), "email": invited["email"], "role": str(role_id)}, token)
            assert r.status_code in (200, 201), f"Invite user failed: {r.text}"

    # Get or create project
    r = api_get(f"/projects/?org_id={org_id}", token)
    if r.json():
        project_id = str(r.json()[0]["project_id"])
        print(f"📁 Found existing project_id: {project_id}")
    else:
        r = api_post("/projects/", {"name": "Project X", "description": "", "org_id": str(org_id)}, token)
        assert r.status_code in (200, 201), f"Create project failed: {r.text}"
        project_id = str(r.json()["project_id"])
        print(f"📁 Created project_id: {project_id}")

    # Add invited user to project
    r = api_get(f"/project-members/?project_id={project_id}", token)
    if invited and "user_id" in invited:
        member_ids = [m.get("user_id") for m in r.json()]
        if invited["user_id"] not in member_ids:
            print(f"👥 Adding invited user to project")
            r = api_post("/project-members/", {
                "user_id": invited["user_id"],
                "project_id": project_id,
                "role": str(role_id)
            }, token)
            assert r.status_code in (200, 201), f"Add user to project failed: {r.text}"

    # Get or create task
    r = api_get(f"/tasks/?project_id={project_id}", token)
    if r.json():
        task_id = str(r.json()[0]["task_id"])
        print(f"📝 Found existing task_id: {task_id}")
    else:
        r = api_post("/tasks/", {
            "title": "Initial Task",
            "description": "Details",
            "project_id": project_id
        }, token)
        assert r.status_code in (200, 201), f"Create task failed: {r.text}"
        task_id = str(r.json()["task_id"])
        print(f"📝 Created task_id: {task_id}")

    # Comments
    r = api_get(f"/task-comments/?task_id={task_id}", token)
    if len(r.json()) == 0:
        r = api_post("/task-comments/", {"task_id": task_id, "comment": "First comment"}, token)
        assert r.status_code in (200, 201), f"Create comment failed: {r.text}"
        print("💬 Added first comment")

    # Attachments
    r = api_get(f"/task-attachments/?task_id={task_id}", token)
    if len(r.json()) == 0:
        r = api_post("/task-attachments/", {"task_id": task_id, "attachment": "First attachment"}, token)
        assert r.status_code in (200, 201), f"Create attachment failed: {r.text}"
        print("📎 Added first attachment")

    # History
    r = api_get(f"/task-history/?task_id={task_id}", token)
    if len(r.json()) == 0:
        r = api_post("/task-history/", {"task_id": task_id, "comment": "First comment"}, token)
        assert r.status_code in (200, 201), f"Create task history failed: {r.text}"
        print("📜 Added first task history entry")

    print(f"\n✅ Flow completed for org_id: {org_id}, project_id: {project_id}, task_id: {task_id}")
    return org_id, project_id, task_id





# from models.enums import DesignationEnum, RoleEnum
# import pytest
# from fastapi.testclient import TestClient
# from main import app
# import jwt
# import time
# import os
# import uuid
# from dotenv import load_dotenv

# load_dotenv()

# client = TestClient(app)
# SUPABASE_SECRET_KEY = os.getenv("SUPABASESECRETKEYST")
# assert SUPABASE_SECRET_KEY, "SUPABASE_SECRET_KEY is not set"
# ALGORITHM = "HS256"


# # -------- Utilities --------

# def create_jwt_token(user_id: str, expire_seconds=3600):
#     now = int(time.time())
#     payload = {
#         "sub": user_id,
#         "iat": now,
#         "exp": now + expire_seconds,
#         "aud": "authenticated"
#     }
#     token = jwt.encode(payload, SUPABASE_SECRET_KEY, algorithm=ALGORITHM)
#     return f"Bearer {token}"


# def generate_user(prefix="user"):
#     if prefix == "existing":
#         uid = "157901b5-df3f-487f-872d-bdeb4d3ba959"
#     else:       
#         uid = str(uuid.uuid4())
#     return {
#         "user_id": uid,
#         "username": f"{prefix}_{uid}",
#         "email": f"{prefix}_{uid}@example.com"
#     }


# # -------- Fixtures --------

# @pytest.fixture
# def creator_user():
#     user = generate_user("creator")
#     return {"user": user}


# @pytest.fixture
# def invited_user():
#     user = generate_user("invited")
#     return {"user": user}

# @pytest.fixture
# def existing_user():
#     user = generate_user("existing")
#     return {"user": user}


# # -------- API Helpers --------

# base_path = '/v1/routes'  # Add leading slash for safety


# def api_post(path, data, token):
#     return client.post(base_path + path, json=data, headers={"Authorization": token})


# def api_get(path, token):
#     return client.get(base_path + path, headers={"Authorization": token})


# def api_put(path, token):
#     return client.put(base_path + path, headers={"Authorization": token})


# def api_delete(path, token):
#     return client.delete(base_path + path, headers={"Authorization": token})


# # -------- Full Flow Test --------

# def test_start_flow(creator_user, invited_user, existing_user):
#     full_user_org_flow(existing_user, invited_user)
#     # full_user_org_flow(creator_user, invited_user)
#     full_user_org_flow(invited_user, {})  # invited_user has no invites at first


# def full_user_org_flow(creator_user, invited_user):
#     creator = creator_user["user"]
#     invited = invited_user.get("user") if isinstance(invited_user, dict) else None
#     token = create_jwt_token(creator["user_id"])

#     # Register creator
#     r = api_post("/register", creator, token)
#     assert r.status_code in (200, 201), f"Creator register failed: {r.text}"

#     # Login
#     r = api_post("/login", {"identifier": creator["username"]}, token)
#     assert r.status_code in (200, 201), f"Login failed: {r.text}"
#     assert r.json()["username"] == creator["username"]

#     # Get organization invites
#     r = api_get("/organization-invites/user", token)
#     assert r.status_code == 200, f"Get invites failed: {r.text}"

#     invites = r.json()
#     if invites:
#         invite = invites[0]
#         # Make sure IDs are strings for URL path
#         invite_id = str(invite.get("invite_id"))
#         org_id = str(invite.get("org_id"))
#         assert invite_id and org_id, f"Invite or org id missing in invite: {invite}"
#         r = api_put(f"/organization-invites/{invite_id}/accept?org_id={org_id}", token)
#         assert r.status_code in (200, 201), f"Accept invite failed: {r.text}"

#     # Get or create organization
#     r = api_get("/organizations/", token)
#     assert r.status_code == 200, f"Get organizations failed: {r.text}"
#     if r.json():
#         org_id = str(r.json()[0]["org_id"])
#     else:
#         org_name = "Org_" + uuid.uuid4().hex[:6]
#         r = api_post("/organizations/", {"name": org_name, "description": "Test Org"}, token)
#         assert r.status_code in (200, 201), f"Create org failed: {r.text}"
#         org_id = str(r.json()["org_id"])

#     # Invite user if invited user info exists
#     r = api_get(f"/organization-members/?org_id={org_id}", token)
#     assert r.status_code == 200, f"Get org members failed: {r.text}"

#     if invited and "email" in invited:
#         member_emails = [m.get("email") for m in r.json()]
#         if invited["email"] not in member_emails:
#             # r = api_post("/organization-invites/", {"org_id": org_id, "email": invited["email"], "role": RoleEnum.MEMBER, "designation": DesignationEnum.DEVELOPER}, token)
#             r = api_post("/organization-invites/", {"org_id": org_id, "email": invited["email"]}, token)

#             assert r.status_code in (200, 201), f"Invite user failed: {r.text}"

#     # Create or get project
#     r = api_get(f"/projects/?org_id={org_id}", token)
#     assert r.status_code == 200, f"Get projects failed: {r.text}"
#     if r.json():
#         project_id = str(r.json()[0]["project_id"])
#     else:
#         r = api_post("/projects/", {"name": "Project X", "description": "", "org_id": org_id}, token)
#         assert r.status_code in (200, 201), f"Create project failed: {r.text}"
#         project_id = str(r.json()["project_id"])

#     # Add invited user to project if not already a member
#     r = api_get(f"/project-members/?project_id={project_id}", token)
#     assert r.status_code == 200, f"Get project members failed: {r.text}"

#     if invited and "user_id" in invited:
#         member_ids = [m.get("user_id") for m in r.json()]
#         if invited["user_id"] not in member_ids:
#             r = api_post("/project-members/", {
#                 "user_id": invited["user_id"],
#                 "project_id": project_id,
#                 "role": "member"
#             }, token)
#             assert r.status_code in (200, 201), f"Add user to project failed: {r.text}"

#     # Create or get task
#     r = api_get(f"/tasks/?project_id={project_id}", token)
#     assert r.status_code == 200, f"Get tasks failed: {r.text}"
#     if r.json():
#         task_id = str(r.json()[0]["task_id"])
#     else:
#         r = api_post("/tasks/", {
#             "title": "Initial Task",
#             "description": "Details",
#             "project_id": project_id
#         }, token)
#         assert r.status_code in (200, 201), f"Create task failed: {r.text}"
#         task_id = str(r.json()["task_id"])

#     # Get task details
#     r = api_get(f"/tasks/{task_id}", token)
#     assert r.status_code == 200, f"Get task failed: {r.text}"
#     assert r.json()["title"] == "Initial Task"

#     # Comments
#     r = api_get(f"/task-comments/?task_id={task_id}", token)
#     assert r.status_code == 200, f"Get task comments failed: {r.text}"
#     if len(r.json()) == 0:
#         r = api_post("/task-comments/", {"task_id": task_id, "comment": "First comment"}, token)
#         assert r.status_code in (200, 201), f"Create comment failed: {r.text}"

#     # Attachments
#     r = api_get(f"/task-attachments/?task_id={task_id}", token)
#     assert r.status_code == 200, f"Get task attachments failed: {r.text}"
#     if len(r.json()) == 0:
#         r = api_post("/task-attachments/", {"task_id": task_id, "attachment": "First attachment"}, token)
#         assert r.status_code in (200, 201), f"Create attachment failed: {r.text}"

#     # History
#     r = api_get(f"/task-history/?task_id={task_id}", token)
#     assert r.status_code == 200, f"Get task history failed: {r.text}"
#     if len(r.json()) == 0:
#         r = api_post("/task-history/", {"task_id": task_id, "comment": "First comment"}, token)
#         assert r.status_code in (200, 201), f"Create task history failed: {r.text}"

#     return org_id, project_id, task_id



# # import pytest
# # from fastapi.testclient import TestClient
# # from main import app
# # import jwt
# # import time
# # import os
# # import uuid
# # from dotenv import load_dotenv

# # load_dotenv()

# # client = TestClient(app)
# # SUPABASE_SECRET_KEY = os.getenv("SUPABASESECRETKEYST")
# # assert SUPABASE_SECRET_KEY, "SUPABASE_SECRET_KEY is not set"
# # ALGORITHM = "HS256"

# # # -------- Utilities --------

# # def create_jwt_token(user_id: str, expire_seconds=3600):
# #     now = int(time.time())
# #     payload = {
# #         "sub": user_id,
# #         "iat": now,
# #         "exp": now + expire_seconds,
# #         "aud": "authenticated"
# #     }
# #     token = jwt.encode(payload, SUPABASE_SECRET_KEY, algorithm=ALGORITHM)
# #     return f"Bearer {token}"

# # def generate_user(prefix="user"):
# #     uid = str(uuid.uuid4())
# #     return {
# #         "user_id": uid,
# #         "username": f"{prefix}_{uid}",
# #         "email": f"{prefix}_{uid}@example.com"
# #     }

# # # -------- Fixtures --------

# # @pytest.fixture
# # def creator_user():
# #     user = generate_user("creator")
# #     # token = create_jwt_token(user["user_id"])
# #     return {"user": user}


# # @pytest.fixture
# # def invited_user():
# #     user = generate_user("invited")
# #     # token = create_jwt_token(user["user_id"])
# #     return {"user": user}

# # # -------- API Helpers --------

# # base_path = 'v1/routes' 

# # def api_post(path, data, token):
# #     return client.post(base_path+path, json=data, headers={"Authorization": token})

# # def api_get(path, token):
# #     return client.get(base_path+path, headers={"Authorization": token})

# # def api_put(path, token):
# #     return client.put(base_path+path, headers={"Authorization": token})

# # def api_delete(path, token):
# #     return client.delete(base_path+path, headers={"Authorization": token})

# # # -------- Full Flow Test --------

# # def test_start_flow(creator_user, invited_user):
# #     full_user_org_flow(creator_user, invited_user)
# #     full_user_org_flow(invited_user,{})

# # def full_user_org_flow(creator_user, invited_user):
# #     creator = creator_user["user"]
# #     invited = invited_user["user"]
# #     token = create_jwt_token(creator["user_id"])

# #     # Register
# #     r = api_post("/register", creator, token)
# #     assert r.status_code in (200, 201), f"Creator register failed: {r.text}"

# #     # Login
# #     r = api_post("/login", {"identifier": creator["username"]}, token)
# #     assert r.status_code in (200, 201)
# #     assert r.json()["username"] == creator["username"]

# #     # Get users
# #     # r = api_get("/users/", token)
# #     # assert r.status_code == 200
# #     # assert any(u["user_id"] == creator["user_id"] for u in r.json())

# #     # Get invites
# #     r = api_get("/organization-invites/", token)
# #     assert r.status_code == 200
# #     if r.json():
# #         invite = r.json()[0]
# #         r = api_put(f"/organization-invites/{invite['invite_id']}/accept?org_id={invite['org_id']}", token)
# #         assert r.status_code in (200, 201)

# #     # Get or create org
# #     r = api_get("/organizations/", token)
# #     assert r.status_code == 200
# #     if r.json():
# #         org_id = r.json()[0]["org_id"]
# #     else:
# #         org_name = "Org_" + uuid.uuid4().hex[:6]
# #         r = api_post("/organizations/", {"name": org_name, "description": "Test Org"}, token)
# #         assert r.status_code in (200, 201)
# #         org_id = r.json()["org_id"]

# #     # Invite user
# #     r = api_get(f"/organization-members/?org_id={org_id}", token)
# #     assert r.status_code == 200
# #     if isinstance(invited, dict) and "user" in invited and "email" in invited["user"] and not any(m["email"] == invited["email"] for m in r.json()):
# #         r = api_post("/organization-invites/", {"org_id": org_id, "email": invited["email"]}, token)
# #         assert r.status_code in (200, 201)

# #     # Create project
# #     r = api_get(f"/projects/?org_id={org_id}", token)
# #     assert r.status_code == 200
# #     if r.json():
# #         project_id = r.json()[0]["project_id"]
# #     else:
# #         r = api_post("/projects/", {"name": "Project X", "description": "", "org_id": org_id}, token)
# #         assert r.status_code in (200, 201)
# #         project_id = r.json()["project_id"]

# #     # Add user to project
# #     r = api_get(f"/project-members/?project_id={project_id}", token)
# #     assert r.status_code == 200
# #     if isinstance(invited, dict) and "user" in invited and "user_id" in invited["user"] and not any(m["user_id"] == invited["user_id"] for m in r.json()):
# #         r = api_post("/project-members/", {
# #             "user_id": invited["user_id"],
# #             "project_id": project_id,
# #             "role": "member"
# #         }, token)
# #         assert r.status_code in (200, 201)

# #     # Create task
# #     r = api_get(f"/tasks/?project_id={project_id}", token)
# #     assert r.status_code == 200
# #     if r.json():
# #         task_id = r.json()[0]["task_id"]
# #     else:
# #         r = api_post("/tasks/", {
# #             "title": "Initial Task",
# #             "description": "Details",
# #             "project_id": project_id
# #         }, token)
# #         assert r.status_code in (200, 201)
# #         task_id = r.json()["task_id"]

# #     # Get task
# #     r = api_get(f"/tasks/{task_id}", token)
# #     assert r.status_code == 200
# #     assert r.json()["title"] == "Initial Task"

# #     # Comment
# #     r = api_get(f"/task-comments/?task_id={task_id}", token)
# #     assert r.status_code == 200
# #     if len(r.json()) == 0:
# #         r = api_post("/task-comments/", {"task_id": task_id, "comment": "First comment"}, token)
# #         assert r.status_code in (200, 201)

# #     # Attachment
# #     r = api_get(f"/task-attachments/?task_id={task_id}", token)
# #     assert r.status_code == 200
# #     if len(r.json()) == 0:
# #         r = api_post("/task-attachments/", {"task_id": task_id, "attachment": "First attachment"}, token)
# #         assert r.status_code in (200, 201)

# #     # History
# #     r = api_get(f"/task-history/?task_id={task_id}", token)
# #     assert r.status_code == 200
# #     if len(r.json()) == 0:
# #         r = api_post("/task-history/", {"task_id": task_id, "comment": "First comment"}, token)
# #         assert r.status_code in (200, 201)

# #     return org_id, project_id, task_id


# # # def test_full_user_org_flow(creator_user, invited_user):
# # #     token = create_jwt_token(creator_user["user_id"])
# # #     # token = creator_user["token"]
# # #     # invited_token = invited_user["token"]

# # #     # Register creator
# # #     r = api_post("/register", creator_user["user"], token)
# # #     assert r.status_code in (200, 201), f"Creator register failed: {r.text}"

# # #     # login
# # #     r = api_post("/login", {"identifier": creator_user["user"]["username"]}, token)
# # #     assert r.status_code in (200, 201)
# # #     assert r.json()["username"] == creator_user["user"]["username"]
# # #     assert r.json()["email"] == creator_user["user"]["email"]
# # #     assert r.json()["user_id"] == creator_user["user"]["user_id"]

# # #     # get user
# # #     r = api_get("/users/", token)
# # #     assert r.status_code == 200
# # #     assert len(r.json()) == 1
# # #     assert r.json()[0]["username"] == creator_user["user"]["username"]
# # #     assert r.json()[0]["email"] == creator_user["user"]["email"]
# # #     assert r.json()[0]["user_id"] == creator_user["user"]["user_id"] 


# # #     # get user organization invites
# # #     r = api_get("/organization-invites/", token)
# # #     assert r.status_code == 200
# # #     assert len(r.json()) == 0

# # #     # accept first invite if present
# # #     if r.json():
# # #         r = api_put(f"/organization-invites/{r.json()[0]['invite_id']}/accept?org_id={r.json()[0]['org_id']}", token)
# # #         assert r.status_code in (200, 201)

# # #     # get user organizations
# # #     r = api_get("/organizations/", token)
# # #     assert r.status_code == 200
# # #     assert len(r.json()) == 0

# # #     # get user projects if organization exists
# # #     if r.json():
# # #         org_id = r.json()[0]["org_id"]
# # #     else:
# # #         # Create org
# # #         org_name = "Org_" + uuid.uuid4().hex[:6]
# # #         r = api_post("/organizations/", {"name": org_name, "description": "Test Org"}, token)
# # #         assert r.status_code in (200, 201)
# # #         org_id = r.json()["org_id"]

# # #     # Verify member in org
# # #     r = api_get(f"/organization-members/?org_id={org_id}", token)
# # #     assert r.status_code == 200
# # #     # assert invited_user["user"]["email"] in [m["email"] for m in r.json()]

# # #     if len(r.json()) < 2 and invited_user and invited_user["user"] and invited_user["user"]["email"]:
# # #         # Invite user
# # #         invite_email = invited_user["user"]["email"]
# # #         r = api_post("/organization-invites/", {"org_id": org_id, "email": invite_email}, token)
# # #         assert r.status_code in (200, 201)
# # #         invite_id = r.json()["invite_id"]

# # #     r = api_get(f"/projects/?org_id={org_id}", token)
# # #     assert r.status_code == 200
# # #     assert len(r.json()) == 0

# # #     if r.json():
# # #         project_id = r.json()[0]["project_id"]
# # #     else:
# # #         # Create project
# # #         r = api_post("/projects/", {"name": "Project X", "description": "", "org_id": org_id}, token)
# # #         assert r.status_code in (200, 201)
# # #         project_id = r.json()["project_id"]

# # #     # Verify member in project
# # #     r = api_get(f"/project-members/?project_id={project_id}", token)
# # #     assert r.status_code == 200
# # #     # assert invited_user["user"]["email"] in [m["email"] for m in r.json()]

# # #     if len(r.json()) < 2 and invited_user and invited_user["user"] and invited_user["user"]["user_id"]:
# # #         # Add to project
# # #         invited_user_id = invited_user["user"]["user_id"]
# # #         r = api_post("/project-members/", {"user_id": invited_user_id, "project_id": project_id, "role": "member"}, token)
# # #         assert r.status_code in (200, 201)

# # #     r = api_get(f"/tasks/?project_id={project_id}", token)
# # #     assert r.status_code == 200
# # #     assert len(r.json()) == 0

# # #     if r.json():
# # #         task_id = r.json()[0]["task_id"]
# # #     else:
# # #         # Create task
# # #         r = api_post("/tasks/", {"title": "Initial Task", "description": "Details", "project_id": project_id}, token)
# # #         assert r.status_code in (200, 201)
# # #         task_id = r.json()["task_id"]

# # #     # get task
# # #     r = api_get(f"/tasks/{task_id}", token)
# # #     assert r.status_code == 200
# # #     assert r.json()["title"] == "Initial Task"
# # #     assert r.json()["description"] == "Details"
# # #     assert r.json()["project_id"] == project_id

# # #     # get task comments
# # #     r = api_get(f"/task-comments/?task_id={task_id}", token)
# # #     assert r.status_code == 200
# # #     assert len(r.json()) == 0
# # #     assert len(r.json()) == 1
# # #     assert r.json()[0]["comment"] == "First comment"

# # #     if len(r.json()) == 0:
# # #         # Add comment
# # #         r = api_post("/task-comments/", {"task_id": task_id, "comment": "First comment"}, token)
# # #         assert r.status_code in (200, 201)
    
# # #     # get task attachments
# # #     r = api_get(f"/task-attachments/?task_id={task_id}", token)
# # #     assert r.status_code == 200
# # #     assert len(r.json()) == 0

# # #     if len(r.json()) == 0:
# # #         # Create task attachment
# # #         r = api_post("/task-attachments/", {"task_id": task_id, "attachment": "First attachment"}, token)
# # #         assert r.status_code in (200, 201)    

# # #     # get task history
# # #     r = api_get(f"/task-history/?task_id={task_id}", token)
# # #     assert r.status_code == 200
# # #     assert len(r.json()) == 0

# # #     if len(r.json()) == 0:
# # #         # Create task history
# # #         r = api_post("/task-history/", {"task_id": task_id, "comment": "First comment"}, token)
# # #         assert r.status_code in (200, 201)

# # #     # Cleanup
# # #     # api_delete(f"/projects/{project_id}", token)
# # #     # api_delete(f"/organizations/{org_id}", token)
