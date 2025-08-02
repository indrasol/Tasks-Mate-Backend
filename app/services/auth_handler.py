import base64
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, Header
from app.config.settings import SUPABASE_SECRET_KEY, SUPABASE_API_KEY
from fastapi import FastAPI
from app.utils.logger import log_info
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation
import jwt
from fastapi import Depends
from fastapi.security import APIKeyHeader
import time
import datetime

app = FastAPI()

ALGORITHM = "HS256"


async def verify_token(authorization: str = Header(None), is_registration: bool = False):
    try:
        if not authorization or " " not in authorization:
            raise HTTPException(status_code=401, detail="Malformed authorization header")

        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")

        # Decode token for timestamp info (optional, for logs)
        try:
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            # log_info(f"Token iat: {unverified_payload.get('iat')}")
            # log_info(f"Token exp: {unverified_payload.get('exp')}")
        except Exception:
            pass

        # Verify token
        payload = jwt.decode(
            token,
            SUPABASE_SECRET_KEY,
            algorithms=["HS256"],
            audience="authenticated",
            options={"leeway": 10, "verify_iat": False},
        )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        log_info(f"Token valid for user: {user_id}")

        # Get user from your users table
        supabase = get_supabase_client()

        def user_op():
            return supabase.from_("users").select("*").eq("id", user_id).execute()

        user_response = await safe_supabase_operation(user_op, "User lookup failed")

        if is_registration and not user_response.data:
            return {"id": user_id}

        if not user_response.data:
            raise HTTPException(status_code=404, detail="User not found")

        user_data = user_response.data[0]
        return {
            "id": user_id,
            "username": user_data["username"],
            "email": user_data["email"]
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        log_info(f"Token verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication failed")


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != SUPABASE_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key
