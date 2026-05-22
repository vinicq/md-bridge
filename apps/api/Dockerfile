# syntax=docker/dockerfile:1.7

# Base image carries Python 3.12+ plus Playwright/Chromium and all the system
# libraries Chromium needs at runtime. Building from scratch would otherwise
# require manually installing fonts, libnss3, etc.

# ---- Stage 1: base ---------------------------------------------------------
# Shared between runtime and test targets so dependencies and source are
# installed exactly once.
FROM mcr.microsoft.com/playwright/python:v1.60.0-noble@sha256:8ff591d613b01c884cc488339ed4318b4513eaf0c57a164a878ba49e70e3f384 AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install Python dependencies first so the layer cache survives source changes.
COPY apps/api/pyproject.toml /app/apps/api/pyproject.toml
COPY apps/api/app/__init__.py /app/apps/api/app/__init__.py
RUN pip install -e /app/apps/api

# Vendored converter packages the API imports at runtime.
COPY packages /app/packages

# Application source.
COPY apps/api/app /app/apps/api/app

# ---- Stage 2: runtime (default) --------------------------------------------
# Lean production image: only runtime dependencies, no tests.
FROM base AS runtime

EXPOSE 8000

# Bind on 0.0.0.0 so the port is reachable from outside the container.
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--app-dir", "/app/apps/api"]

# ---- Stage 3: runtime-ocr (optional) ---------------------------------------
# Opt-in production image with Tesseract available for scanned PDFs.
FROM runtime AS runtime-ocr

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-por \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -e "/app/apps/api[ocr]"

# ---- Stage 4: test ---------------------------------------------------------
# Adds dev dependencies (pytest, httpx, ruff) and the test trees so the suite
# can run inside Docker via the compose `test` profile.
FROM base AS test

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-por \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -e "/app/apps/api[dev,ocr]"

COPY apps/api/tests /app/apps/api/tests
COPY tests /app/tests

WORKDIR /app

CMD ["python", "-m", "pytest", "apps/api/tests", "tests"]
