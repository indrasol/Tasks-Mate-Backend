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

        # Extract and validate the scheme and token
        try:
            scheme, token = authorization.strip().split(" ", 1)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid authorization format")

        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")

        if not isinstance(token, str) or not token:
            raise HTTPException(status_code=401, detail="Token must be a non-empty string")
        
        if not isinstance(SUPABASE_SECRET_KEY, str):
            raise HTTPException(status_code=500, detail=f"Server misconfiguration: Invalid secret key - {SUPABASE_SECRET_KEY}")


        # Decode token without verifying to log iat/exp (optional)
        try:
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            # log_info(f"Unverified token iat: {unverified_payload.get('iat')}, exp: {unverified_payload.get('exp')}")
        except Exception as decode_err:
            log_info(f"Could not decode unverified token payload: {decode_err}")

        # Fully verify token
        try:
            payload = jwt.decode(
                token,
                SUPABASE_SECRET_KEY,
                algorithms=["HS256"],
                audience="authenticated",
                options={"leeway": 10, "verify_iat": False}
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

        user_id = payload.get("sub")
        if not user_id or not isinstance(user_id, str):
            raise HTTPException(status_code=401, detail="Invalid token payload: missing user ID")

        log_info(f"Token valid for user ID: {user_id}")

        # Look up user in Supabase
        supabase = get_supabase_client()

        def user_op():
            return supabase.from_("users").select("username,email").eq("id", user_id).execute()

        user_response = await safe_supabase_operation(user_op, "User lookup failed")

        if is_registration:
            # During registration, allow the user to not exist yet
            return {"id": user_id}

        if not user_response.data:
            raise HTTPException(status_code=404, detail="User not found")

        user_data = user_response.data[0]
        return {
            "id": user_id,
            "username": user_data.get("username"),
            "email": user_data.get("email")
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
