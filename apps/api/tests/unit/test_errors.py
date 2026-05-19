"""Pure-function tests of the error envelope plumbing."""
from __future__ import annotations

import asyncio

from app.errors import (
    ApiError,
    api_error_handler,
    http_exception_handler,
    validation_exception_handler,
)
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError


def _decode(response) -> dict:
    return _json_loads(response.body)


def _json_loads(raw) -> dict:
    import json

    return json.loads(raw)


def test_api_error_carries_code_message_and_optional_detail():
    err = ApiError(400, "wrong_file_type", "no PDF here", detail={"got": "txt"})
    assert err.status_code == 400
    assert err.code == "wrong_file_type"
    assert err.message == "no PDF here"
    assert err.extra_detail == {"got": "txt"}


def test_api_error_handler_renders_envelope_with_detail():
    err = ApiError(413, "payload_too_large", "way too big", detail={"limit_mb": 50})
    resp = asyncio.run(api_error_handler(None, err))  # type: ignore[arg-type]
    body = _decode(resp)
    assert resp.status_code == 413
    assert body == {
        "error": {
            "code": "payload_too_large",
            "message": "way too big",
            "detail": {"limit_mb": 50},
        }
    }


def test_api_error_handler_omits_detail_when_absent():
    err = ApiError(400, "x", "y")
    resp = asyncio.run(api_error_handler(None, err))  # type: ignore[arg-type]
    body = _decode(resp)
    assert body == {"error": {"code": "x", "message": "y"}}


def test_http_exception_handler_maps_known_status_to_code():
    exc = HTTPException(status_code=404, detail="missing")
    resp = asyncio.run(http_exception_handler(None, exc))  # type: ignore[arg-type]
    body = _decode(resp)
    assert resp.status_code == 404
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "missing"


def test_http_exception_handler_falls_back_to_generic_code():
    exc = HTTPException(status_code=418, detail="teapot")
    resp = asyncio.run(http_exception_handler(None, exc))  # type: ignore[arg-type]
    body = _decode(resp)
    assert body["error"]["code"] == "error"


def test_validation_exception_handler_surfaces_pydantic_errors():
    # Build a RequestValidationError with a minimal but realistic payload.
    errors = [
        {"loc": ("body", "page_break"), "msg": "Input should be a valid boolean", "type": "bool_type"}
    ]
    exc = RequestValidationError(errors=errors)
    resp = asyncio.run(validation_exception_handler(None, exc))  # type: ignore[arg-type]
    body = _decode(resp)
    assert resp.status_code == 422
    assert body["error"]["code"] == "invalid_input"
    assert isinstance(body["error"]["detail"], list)
    assert body["error"]["detail"][0]["msg"] == "Input should be a valid boolean"
