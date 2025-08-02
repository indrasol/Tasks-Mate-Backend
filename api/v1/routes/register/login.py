from fastapi import APIRouter, HTTPException
# from datetime import timedelta
from utils.logger import log_info
from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordRequestForm
from core.db.supabase_db import get_supabase_client, safe_supabase_operation
from services.auth_handler import verify_token, verify_api_key
import re
import traceback


router = APIRouter()

@router.post("/get-email")
async def get_email(request_data: dict, api_key: str = Depends(verify_api_key)):
    username = request_data.get("username")
    try:
        supabase_client = get_supabase_client()
        def user_operation():
            return supabase_client.from_("users").select("email").eq("username", username).execute()
        user_response = await safe_supabase_operation(
            user_operation,
            "Failed to fetch email for the username"
        )
        log_info(f"User response: {user_response}")
        return {"message": "Email fetched successfully", "email": user_response.data[0].get("email")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch email for the username: {str(e)}")
    


@router.post("/login")
async def login(identifier: dict, current_user: dict = Depends(verify_token)):
    supabase = get_supabase_client()
    try:
        field = "email" if "@" in identifier.get("identifier") else "username"

        def get_user():
            return supabase.from_("users").select("*").eq(field, identifier["identifier"]).execute()

        user_response = await safe_supabase_operation(get_user, "User lookup failed")

        if not user_response.data:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        else:
            user_data = user_response.data[0]

        return {
            "message": "User authenticated",
            "user_id": user_data["id"],
            "username": user_data["username"],
            "email": user_data["email"]
        }

    except Exception as e:
        log_info(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")
