"""Uniform error envelope.

Every failure response carries `{"error": {"code", "message", "detail"?}}`.
"""
from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class ApiError(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        detail: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=message, headers=headers)
        self.code = code
        self.message = message
        self.extra_detail = detail


def _envelope(code: str, message: str, detail: Any | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"error": {"code": code, "message": message}}
    if detail is not None:
        body["error"]["detail"] = detail
    return body


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(exc.code, exc.message, exc.extra_detail),
        headers=exc.headers,
    )


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    code = {
        400: "bad_request",
        404: "not_found",
        413: "payload_too_large",
        422: "invalid_input",
        504: "timeout",
    }.get(exc.status_code, "error")
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(code, str(exc.detail)),
    )


async def validation_exception_handler(_: Request, exc) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=_envelope("invalid_input", "Validation failed", detail=exc.errors()),
    )
