
from typing import List
from app.core.db.supabase_db import get_supabase_client, safe_supabase_operation

async def get_user_details_by_id(user_id: str):
    return await get_combined_user_details(user_id)

async def get_user_details_by_username(username: str):
    return await get_combined_user_details(None, username)

async def get_combined_user_details(user_id: str = None, username: str = None):
    """
    Fetch user details from both public.users and auth.users.
    You must provide either user_id or username.
    """
    if not user_id and not username:
        raise ValueError("Either user_id or username must be provided.")

    supabase = get_supabase_client()

    # Helper to get user from public.users
    # async def get_from_users_table():
    #     def op():
    #         query = supabase.from_("users").select("*")
    #         if user_id:
    #             query = query.eq("id", user_id)
    #         elif username:
    #             query = query.eq("username", username)
    #         return query.single().execute()

    #     return await safe_supabase_operation(op, "Failed to fetch user from public.users")

    # Helper to get user from auth.users
    async def get_from_auth_users():
        def op():            
            if user_id:
                return supabase.rpc("get_auth_user", {"p_user_id": user_id}).limit(1).execute()
            elif username:
                return supabase.rpc("get_auth_user", {"p_username": username}).limit(1).execute()

        return await safe_supabase_operation(op, "Failed to fetch user from auth.users")

    # Fetch both
    # user_result = await get_from_users_table()
    auth_result = await get_from_auth_users()

    user_details = {}

    # Prefer username/email from public.users if available
    # if user_result and user_result.data:
    #     data = user_result.data
    #     user_details["id"] = data.get("id")
    #     user_details["username"] = data.get("username")
    #     user_details["email"] = data.get("email")
    
    if auth_result and auth_result.data and len(auth_result.data) > 0 :
        data = auth_result.data[0]
        user_details["id"] = data.get("id")
        user_details["email"] = data.get("email")
        user_details["username"] = data.get("username") or data.get("user_metadata", {}).get("username")

    return user_details



# async def get_user_details_by_id(user_id: str):
#     """Fetch a single username from the users table for the given user_id."""
#     supabase = get_supabase_client()
#     def op():
#         return (
#             supabase
#             .from_("users")
#             .select("*")
#             .eq("id", user_id)
#             .single()
#             .execute()
#         )
#     result = await safe_supabase_operation(op, "Failed to fetch user by id")
#     user_details = {}
#     if result and result.data:
#         user_details["username"] = result.data["username"]
#         user_details["email"] = result.data["email"]
#         user_details["id"] = result.data["id"]
#     return user_details

# async def get_user_details_by_username(username: str):
#     """Fetch a single username from the users table for the given user_id."""
#     supabase = get_supabase_client()
#     def op():
#         return (
#             supabase
#             .from_("users")
#             .select("*")
#             .eq("username", username)
#             .single()
#             .execute()
#         )
#     result = await safe_supabase_operation(op, "Failed to fetch user by username")
#     user_details = {}
#     if result and result.data:
#         user_details["username"] = result.data["username"]
#         user_details["email"] = result.data["email"]
#         user_details["id"] = result.data["id"]
#     return user_details



