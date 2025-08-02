# 1) Build stage for Azure Web App (x86_64)
FROM python:3.11-slim AS base

WORKDIR /src

# Install system dependencies (curl for health check)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create /app directory and move project files into it
COPY . /app
RUN mv /app/* /app/.* /src/ 2>/dev/null || true && rm -rf /app

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

# Expose the port
EXPOSE ${PORT}

# Startup command (updated to app.main:tm_app; uses env var for port)
CMD ["gunicorn", "--workers=2", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:${PORT}", "--timeout", "120", "--access-logfile", "-", "app.main:tm_app"]
