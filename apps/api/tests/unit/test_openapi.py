"""The custom OpenAPI builder documents optional API-key auth and keeps the
app metadata FastAPI's default builder would include."""
from __future__ import annotations

from app.main import create_app


def test_documents_optional_api_key():
    schema = create_app().openapi()
    assert "APIKeyHeader" in schema["components"]["securitySchemes"]
    security = schema["paths"]["/api/md-to-pdf"]["post"]["security"]
    assert {} in security  # no-auth alternative: not mandatory on an open deploy
    assert {"APIKeyHeader": []} in security


def test_keeps_contact_and_license():
    info = create_app().openapi()["info"]
    assert info["contact"]["name"] == "md-bridge"
    assert info["license"]["name"] == "MIT"
