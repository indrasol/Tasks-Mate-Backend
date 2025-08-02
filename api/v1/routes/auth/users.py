from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
import os
import requests
import jwt

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
SUPABASE_AUTH_URL = f"{SUPABASE_URL}/auth/v1"

if not all([SUPABASE_URL, SUPABASE_KEY, SUPABASE_JWT_SECRET]):
    raise RuntimeError("One or more required environment variables are missing.")

# -------- Models --------

class RegisterRequest(BaseModel):
    email: str
    password: str
    username: str

class LoginRequest(BaseModel):
    identifier: str  # email or username
    password: str

class TokenVerifyRequest(BaseModel):
    token: str

class ResetPasswordRequest(BaseModel):
    email: str

# -------- /register --------
@router.post("/register")
def register_user(payload: RegisterRequest):
    resp = requests.post(
        f"{SUPABASE_AUTH_URL}/admin/users",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        },
        json={
            "email": payload.email,
            "password": payload.password,
            "email_confirm": True,
            "user_metadata": {
                "username": payload.username
            }
        }
    )

    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())

    return {
        "message": "User registered",
        "user_id": resp.json()["id"]
    }

# -------- /login --------
@router.post("/login")
def login_user(payload: LoginRequest):
    identifier = payload.identifier
    password = payload.password

    # Resolve identifier
    if "@" in identifier:
        email = identifier
    else:
        users_resp = requests.get(
            f"{SUPABASE_AUTH_URL}/admin/users",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            }
        )

        if not users_resp.ok:
            raise HTTPException(status_code=500, detail="Could not fetch users")

        users = users_resp.json()
        matched_user = next((u for u in users if u.get("user_metadata", {}).get("username") == identifier), None)
        if not matched_user:
            raise HTTPException(status_code=404, detail="Username not found")
        email = matched_user["email"]

    # Login with email/password
    token_resp = requests.post(
        f"{SUPABASE_AUTH_URL}/token?grant_type=password",
        headers={"apikey": SUPABASE_KEY},
        data={"email": email, "password": password}
    )

    if not token_resp.ok:
        raise HTTPException(status_code=401, detail=token_resp.json())

    return token_resp.json()

# -------- /logout --------
@router.post("/logout")
def logout_user(refresh_token: str = Header(...)):
    resp = requests.post(
        f"{SUPABASE_AUTH_URL}/logout",
        headers={"apikey": SUPABASE_KEY},
        json={"refresh_token": refresh_token}
    )
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return {"message": "Logged out successfully"}

# -------- /token/verify --------
@router.post("/token/verify")
def verify_token(payload: TokenVerifyRequest):
    try:
        decoded = jwt.decode(payload.token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
        return {"valid": True, "claims": decoded}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# -------- /reset-password --------
@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest):
    resp = requests.post(
        f"{SUPABASE_AUTH_URL}/recover",
        headers={"apikey": SUPABASE_KEY},
        json={"email": payload.email}
    )

    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return {"message": "Password reset email sent"}
