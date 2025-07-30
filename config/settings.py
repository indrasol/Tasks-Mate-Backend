import os
from dotenv import load_dotenv

load_dotenv()

env = os.getenv('ENV', 'development') 

if env == 'development':
    load_dotenv('.env.dev')
elif env == 'production':
    load_dotenv('.env.prod')

# Main
title=os.getenv("title")
description=os.getenv("description")
version=os.getenv("version")

print(f"title: {title}, description: {description}, version: {version}")

# Allow frontend origins (Update this to match your frontend URL)
# origins = os.getenv("origins").split(",")  # Split comma-separated string into list


# Get the base directory of the entire project (one level up from /config)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Uploads directory
UPLOADS_DIR = os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))

# Output directory
OUTPUT_DIR = os.getenv("OUTPUT_FOLDER", os.path.join(BASE_DIR, "output"))

# Reports directory
REPORTS_DIR = os.getenv("REPORTS_FOLDER", os.path.join(BASE_DIR, "reports"))

# JWT Secret Key
SUPABASE_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# Database
# DB_USER = os.getenv("DB_USER")
# DB_PASSWORD = os.getenv("DB_PASSWORD")
# DB_HOST = os.getenv("DB_HOST")
# DB_PORT = os.getenv("DB_PORT")
# DB_NAME = os.getenv("DB_NAME")

# POSTGRES_DATABASE_URL = os.getenv("POSTGRES_DATABASE_URL")

# SUPABASE_URL = os.getenv("SUPABASE_DB_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_PROJECT_URL = os.getenv("SUPABASEURLST")
SUPABASE_API_KEY = os.getenv("SUPABASEAPIKEYST")
# SUPABASE_SERVICE_KEY = os.getenv("SUPABASESERVICEKEYST")
# SUPABASE_SECRET_KEY = os.getenv("SUPABASESECRETKEYST")

HEALTH_API_KEY = os.getenv("HEALTH_API_KEY")


# Redis settings for session management
# REDIS_HOST = os.getenv("REDISHOSTST")
# REDIS_PORT = os.getenv("REDISPORTST")
# REDIS_PASSWORD = os.getenv("REDISPASSWORDST")
# REDIS_DB = os.getenv("REDISDBST")
SESSION_EXPIRY = os.getenv("SESSIONEXPIRYST")
DATABASE_URL_ASYNC = os.getenv("DATABASEURLASYNCST")
SUPABASE_DATABASE_URL = os.getenv("SUPABASEDATABASEURLST")

# Custom Metrics
METRICS_USERNAME = os.getenv("METRICS_USERNAME")
METRICS_PASSWORD = os.getenv("METRICS_PASSWORD")

SUPABASE_BUCKET_NAME = os.getenv("SUPABASEBUCKETNAME", "taskmate-attachments")
