from supabase import create_client, Client
from app.config.settings import SUPABASE_PROJECT_URL, SUPABASE_API_KEY, SUPABASE_SERVICE_KEY
from fastapi import HTTPException
from app.utils.logger import log_info, log_error, log_debugger
from functools import lru_cache
import asyncio
import httpx
from concurrent.futures import ThreadPoolExecutor


# Global thread pool for running Supabase operations asynchronously
thread_pool = ThreadPoolExecutor()

# Initialize Supabase client
@lru_cache
def get_supabase_client():
    # Prefer service role key on the server for privileged operations (e.g., storage uploads)
    # Fallback to public anon key if service key is not configured
    key_to_use = SUPABASE_SERVICE_KEY or SUPABASE_API_KEY
    log_debugger(f"SUPABASE_PROJECT_URL: {SUPABASE_PROJECT_URL}")
    # Avoid logging the actual secret value
    which_key = "service" if SUPABASE_SERVICE_KEY else "anon"
    log_debugger(f"Using Supabase key type: {which_key}")
    supbase: Client = create_client(SUPABASE_PROJECT_URL, key_to_use)
    return supbase

# Helper to run Supabase operations asynchronously
async def run_supabase_async(func):
    return await asyncio.get_event_loop().run_in_executor(
        thread_pool, func
    )

# Helper for safer Supabase operations with error handling
async def safe_supabase_operation(operation, error_message="Supabase operation failed"):
    try:
        return await run_supabase_async(operation)
    except Exception as e:
        # log_error(f"{error_message}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"{error_message}: {str(e)}")

