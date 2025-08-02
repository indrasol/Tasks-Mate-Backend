# 1) Build stage for Azure Web App (x86_64)
FROM python:3.11-slim AS base

WORKDIR /src

# Install system dependencies (curl for health check)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY app/requirements.txt app/
RUN pip install --no-cache-dir -r app/requirements.txt

<<<<<<< HEAD
# Copy the actual application code
<<<<<<< HEAD
COPY app/ app/
=======
COPY . .
>>>>>>> 6ade0c0 (Update Dockerfile)
=======
# Create /app directory and move project files into it
COPY . /app
RUN mv /app/* /app/.* /src/ 2>/dev/null || true && rm -rf /app
>>>>>>> a075542 (Update Dockerfile)

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /src

USER appuser

# Explicit port for Azure (optional, but ensures consistency)
ENV PORT=8000
ENV PYTHONPATH=/src

# Health check (use /health for faster response)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

<<<<<<< HEAD
# gunicorn will listen on 8000 inside the container
EXPOSE 8000

# Simplified startup command with better error handling
# CMD ["gunicorn", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "main:app"]
<<<<<<< HEAD
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--access-log", "--log-level", "info"]
=======
CMD ["python", "-m", "uvicorn", "main:tm_app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

>>>>>>> 6ade0c0 (Update Dockerfile)
=======
# Expose the port
EXPOSE ${PORT}

# Startup command (updated to app.main:tm_app; uses env var for port)
CMD ["gunicorn", "--workers=2", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:${PORT}", "--timeout", "120", "--access-logfile", "-", "app.main:tm_app"]
>>>>>>> a075542 (Update Dockerfile)
