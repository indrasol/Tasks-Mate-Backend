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


SUPABASE_PROJECT_URL = os.getenv("SUPABASE_URL_TM")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY_TM")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY_TM")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY_TM")

HEALTH_API_KEY = os.getenv("HEALTH_API_KEY")

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY_TM")


# Redis settings for session management
# REDIS_HOST = os.getenv("REDISHOSTST")
# REDIS_PORT = os.getenv("REDISPORTST")
# REDIS_PASSWORD = os.getenv("REDISPASSWORDST")
# REDIS_DB = os.getenv("REDISDBST")
# SESSION_EXPIRY = os.getenv("SESSIONEXPIRYST")
# DATABASE_URL_ASYNC = os.getenv("DATABASEURLASYNCST")
# SUPABASE_DATABASE_URL = os.getenv("SUPABASEDATABASEURLST")

# Custom Metrics
# METRICS_USERNAME = os.getenv("METRICS_USERNAME")
# METRICS_PASSWORD = os.getenv("METRICS_PASSWORD")
