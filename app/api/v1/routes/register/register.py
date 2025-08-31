# routers/router.py
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, Header
import jwt
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from models.db_schema_models import User, Tenant, UserTenantAssociation
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
# from sqlalchemy import insert
from app.models.registration_models import RegisterRequest
from app.utils.logger import log_info
from app.services.auth_handler import verify_api_key
from app.config.settings import SUPABASE_SECRET_KEY
# from fastapi.security import APIKeyHeader
# from functools import partial
import asyncio

router = APIRouter()

async def registration_verify_token(authorization: str = Header(None)) -> Dict:
    """
    Verify JWT token for registration endpoint only.
    
    Args:
        authorization: Authorization header with token
        
    Returns:
        Dict with user ID
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing token")

        # Log and validate authorization header
        log_info(f"Authorization header received: {authorization} (type: {type(authorization)})")
        
        try:
            scheme, token = authorization.strip().split(" ")
            if scheme.lower() != "bearer":
                raise HTTPException(status_code=401, detail="Invalid authorization scheme")
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid authorization header format")

        if not isinstance(token, str):
            raise HTTPException(status_code=401, detail="Token must be a string")

        if not isinstance(SUPABASE_SECRET_KEY, str):
            raise HTTPException(status_code=500, detail="Server misconfiguration: Invalid secret key")

        # Verify the JWT token
        try:
            payload = jwt.decode(
                token,
                SUPABASE_SECRET_KEY,
                algorithms=["HS256"],
                audience="authenticated",
                options={"leeway": 10, "verify_iat": False}
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

        user_id = payload.get("sub")
        if not user_id or not isinstance(user_id, str):
            raise HTTPException(status_code=401, detail="Invalid token payload: Missing or invalid user ID")

        log_info(f"Registration token valid for user ID: {user_id}")

        return {"id": user_id}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        log_info(f"Registration token verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication system error")

@router.post("/register")
async def register(request_data: RegisterRequest, current_user: dict = Depends(registration_verify_token)):
    try:
        supabase = get_supabase_client()
        log_info(f"Supabase client: {supabase}")
        log_info(f"Request data: {request_data}")
        log_info(f"Current user: {current_user}")

        def check_user():
            return supabase.from_("users").select("*").eq("id", request_data.user_id).execute()

        existing = await safe_supabase_operation(check_user, "Check user failed")
        if existing.data:
            raise HTTPException(status_code=400, detail="User already exists")

        new_user_data = {
            "id": request_data.user_id,
            "username": request_data.username,
            "email": request_data.email
        }

        def insert_user():
            return supabase.from_("users").insert(new_user_data).execute()

        await safe_supabase_operation(insert_user, "Insert user failed")

        return {"message": "User registered successfully"}

    except HTTPException as http_exc:
        # Preserve original HTTPException (e.g., 400 already exists)
        raise http_exc
    except Exception as e:
        log_info(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")
    
@router.post("/register_confirm")
async def register_confirm(request_data: RegisterRequest):
    try:
        supabase = get_supabase_client()
        log_info(f"Supabase client: {supabase}")
        log_info(f"Request data: {request_data}")

        def check_user():
            return supabase.from_("users").select("*").eq("id", request_data.user_id).execute()

        existing = await safe_supabase_operation(check_user, "Check user failed")
        if existing.data:
            raise HTTPException(status_code=400, detail="User already exists")

        new_user_data = {
            "id": request_data.user_id,
            "username": request_data.username,
            "email": request_data.email
        }

        def insert_user():
            return supabase.from_("users").insert(new_user_data).execute()

        await safe_supabase_operation(insert_user, "Insert user failed")

        return {"message": "User registered successfully"}

    except HTTPException as http_exc:
        # Preserve original HTTPException (e.g., 400 already exists)
        raise http_exc
    except Exception as e:
        log_info(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")




@router.post("/cleanup-auth-user")
async def cleanup_auth_user(request_data: dict, api_key: str = Depends(verify_api_key)):
    user_id = request_data.get("user_id")
    try:
        supabase = get_supabase_client()
        supabase.auth.admin.delete_user(user_id)
        return {"message": "Auth user deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete auth user: {str(e)}")

# -----------------------------
# Helper: cleanup unconfirmed users after 1 h
# -----------------------------


async def _cleanup_unconfirmed_user(user_id: str):
    """Remove auth and DB records for users who never confirmed e-mail."""
    # Wait 1 hour (3600 s)
    await asyncio.sleep(3600)

    supabase_client = get_supabase_client()

    try:
        # Check if the auth user has confirmed their e-mail yet
        auth_user_resp = supabase_client.auth.admin.get_user_by_id(user_id)
        # Different SDK versions expose the field differently; try both.
        confirmed_at = getattr(auth_user_resp.user, "email_confirmed_at", None)
        if confirmed_at is None and isinstance(auth_user_resp.user, dict):
            confirmed_at = auth_user_resp.user.get("email_confirmed_at")

        if confirmed_at:
            # User confirmed – nothing to do
            log_info(f"User {user_id} confirmed email. Cleanup not required.")
            return

        log_info(f"User {user_id} did NOT confirm email within 1 h – cleaning up.")

        # Delete from user_tenant_association first (FK constraint)
        try:
            supabase_client.from_("user_tenant_association").delete().eq("user_id", user_id).execute()
        except Exception:
            pass

        # Delete from users table
        try:
            supabase_client.from_("users").delete().eq("id", user_id).execute()
        except Exception:
            pass

        # Delete from auth.users
        try:
            supabase_client.auth.admin.delete_user(user_id)
        except Exception:
            pass
    except Exception as e:
        # Log but do not raise, since this is a background task
        log_info(f"Cleanup task error for user {user_id}: {str(e)}")

# -----------------------------
# Pending-registration endpoint
# -----------------------------


@router.post("/register/pending")
async def register_pending(request_data: RegisterRequest, api_key: str = Depends(verify_api_key)):
    try:
        supabase = get_supabase_client()

        new_user_data = {
            "id": request_data.user_id,
            "username": request_data.username,
            "email": request_data.email
        }

        def upsert_user():
            return supabase.from_("users").upsert(new_user_data).execute()

        await safe_supabase_operation(upsert_user, "Insert pending user failed")

        asyncio.create_task(_cleanup_unconfirmed_user(request_data.user_id))

        return {"message": "Pending registration saved"}

    except Exception as e:
        log_info(f"Pending registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Pending registration failed")
