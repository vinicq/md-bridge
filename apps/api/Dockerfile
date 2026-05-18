# syntax=docker/dockerfile:1.7

# Base image carries Python 3.13 plus Playwright/Chromium and all the system
# libraries Chromium needs at runtime. Building from scratch would otherwise
# require manually installing fonts, libnss3, etc.
FROM mcr.microsoft.com/playwright/python:v1.60.0-noble

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install Python dependencies first so the layer cache survives source changes.
COPY apps/api/pyproject.toml /app/apps/api/pyproject.toml
COPY apps/api/app/__init__.py /app/apps/api/app/__init__.py
RUN pip install -e /app/apps/api

# Vendored skills the API imports at runtime.
COPY packages /app/packages

# Application source.
COPY apps/api/app /app/apps/api/app

EXPOSE 8000

# Bind on 0.0.0.0 so the port is reachable from outside the container.
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--app-dir", "/app/apps/api"]
