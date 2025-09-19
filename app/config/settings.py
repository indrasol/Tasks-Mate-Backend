import os
from dotenv import load_dotenv
from pathlib import Path

# First get the environment from ENV variable or default to 'development'
ENV = os.getenv('ENV', 'development')

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load the appropriate .env file based on environment
def load_env_file():
    # First try to load .env.{ENV} file
    env_file = BASE_DIR / f".env.{ENV}"
    if env_file.exists():
        print(f"Loading environment from {env_file}")
        # Force override existing environment variables
        load_dotenv(dotenv_path=env_file, override=True)
        return True
    
    # Fallback to the standard .env file
    default_env_file = BASE_DIR / ".env"
    if default_env_file.exists():
        print(f"Loading environment from {default_env_file}")
        # Force override existing environment variables
        load_dotenv(dotenv_path=default_env_file, override=True)
        return True
    
    # If no env file found
    print(f"Warning: No .env.{ENV} or .env file found")
    return False

# Load environment variables
load_env_file()

# Print environment for debugging
print(f"Running in {ENV} environment")


# Main
title=os.getenv("title_TM")
description=os.getenv("description_TM")
version=os.getenv("version_TM")

# print(f"title: {title}, description: {description}, version: {version}")

# Allow frontend origins (Update this to match your frontend URL)
# origins = os.getenv("origins").split(",")  # Split comma-separated string into list


SUPABASE_PROJECT_URL = os.getenv("SUPABASE_URL_TM")
print(f"SUPABASE_PROJECT_URL: {SUPABASE_PROJECT_URL}")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY_TM")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY_TM")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY_TM")

HEALTH_API_KEY = os.getenv("HEALTH_API_KEY")

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY_TM")
TASKS_ATTACHMENTS_BUCKET_TM = os.getenv("TASKS_ATTACHMENTS_BUCKET_TM")
PROJECT_RESOURCES_BUCKET_TM = os.getenv("PROJECT_RESOURCES_BUCKET_TM")
AVATARS_BUCKET_TM = os.getenv("AVATARS_BUCKET_TM")
BUG_ATTACHMENTS_BUCKET_TM = os.getenv("BUG_ATTACHMENTS_BUCKET_TM")

# Email test mode
EMAIL_TEST_MODE = os.getenv("EMAIL_TEST_MODE", "false").lower() == "true"
EMAIL_TEST_REDIRECT = os.getenv("EMAIL_TEST_REDIRECT", "").strip()  # Optional: redirect all emails here
EMAIL_TEST_SUBJECT_PREFIX = os.getenv("EMAIL_TEST_SUBJECT_PREFIX", "[TEST] ")