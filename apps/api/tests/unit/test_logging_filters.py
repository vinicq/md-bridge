"""Coverage for the uvicorn access-log health filter (#134).

The filter logic is pure and tested directly. The wiring is tested by emitting
records through the real `uvicorn.access` logger and asserting suppression, which
exercises Python's logging pipeline end to end. A TestClient-based check would be
a false positive: TestClient drives the ASGI app directly and never goes through
uvicorn's access logger, so the lines would be absent for the wrong reason.
"""
from __future__ import annotations

import logging

import pytest
from app.logging_filters import (
    HealthAccessFilter,
    install_health_access_filter,
)

# The exact message template uvicorn's AccessFormatter feeds the logger.
UVICORN_MSG = '%s - "%s %s HTTP/%s" %d'


def _record(method: str, path: str, status: int) -> logging.LogRecord:
    return logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=UVICORN_MSG,
        args=("127.0.0.1:54312", method, path, "1.1", status),
        exc_info=None,
    )


def _clear_health_filters(logger: logging.Logger) -> None:
    for f in [f for f in logger.filters if isinstance(f, HealthAccessFilter)]:
        logger.removeFilter(f)


def test_drops_successful_health_probe() -> None:
    assert HealthAccessFilter().filter(_record("GET", "/api/health", 200)) is False


def test_keeps_failing_health_probe() -> None:
    # A failing healthcheck is real signal and must stay visible.
    assert HealthAccessFilter().filter(_record("GET", "/api/health", 503)) is True


def test_keeps_domain_requests() -> None:
    assert HealthAccessFilter().filter(_record("POST", "/api/pdf-to-md", 200)) is True


def test_does_not_silence_similar_prefix() -> None:
    # A future /api/healthcheck route must not be swept up by the filter.
    assert HealthAccessFilter().filter(_record("GET", "/api/healthcheck", 200)) is True


@pytest.fixture
def access_logger() -> logging.Logger:
    logger = logging.getLogger("uvicorn.access")
    _clear_health_filters(logger)
    yield logger
    _clear_health_filters(logger)


def test_install_adds_filter_by_default(
    access_logger: logging.Logger, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MD_BRIDGE_LOG_HEALTH", raising=False)
    assert install_health_access_filter() is True
    assert any(isinstance(f, HealthAccessFilter) for f in access_logger.filters)
    # Idempotent: a second call does not stack a duplicate.
    install_health_access_filter()
    assert sum(isinstance(f, HealthAccessFilter) for f in access_logger.filters) == 1


def test_install_respects_env_opt_out(
    access_logger: logging.Logger, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MD_BRIDGE_LOG_HEALTH", "true")
    assert install_health_access_filter() is False
    assert not any(isinstance(f, HealthAccessFilter) for f in access_logger.filters)


def test_filter_suppresses_health_through_the_logging_pipeline(
    access_logger: logging.Logger, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MD_BRIDGE_LOG_HEALTH", raising=False)
    install_health_access_filter()
    access_logger.setLevel(logging.INFO)

    seen: list[str] = []

    class Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            seen.append(record.getMessage())

    handler = Capture()
    access_logger.addHandler(handler)
    try:
        access_logger.info(UVICORN_MSG, "127.0.0.1:1", "GET", "/api/health", "1.1", 200)
        access_logger.info(UVICORN_MSG, "127.0.0.1:1", "POST", "/api/pdf-to-md", "1.1", 200)
        access_logger.info(UVICORN_MSG, "127.0.0.1:1", "GET", "/api/health", "1.1", 503)
    finally:
        access_logger.removeHandler(handler)

    assert not any('"GET /api/health HTTP/1.1" 200' in m for m in seen)
    assert any("/api/pdf-to-md" in m for m in seen)
    # The failing probe survives.
    assert any('"GET /api/health HTTP/1.1" 503' in m for m in seen)
