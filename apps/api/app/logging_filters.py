"""Logging filters for the API process.

The frontend polls `GET /api/health` about once a second, so under a real
conversion batch the `uvicorn.access` log runs roughly 30 healthcheck lines for
every domain request, burying the conversions an operator actually needs to see.
`HealthAccessFilter` drops the successful healthcheck lines while keeping any
4xx/5xx probe visible (a failing healthcheck is real signal).

Filtering is on by default to keep the log slim out of the box. Set
`MD_BRIDGE_LOG_HEALTH=true` to log every request, including health probes.
"""
from __future__ import annotations

import logging
import os

# Match the exact request line uvicorn emits ("GET /api/health HTTP/1.1") rather
# than a bare "/api/health" prefix, so a future route like "/api/healthcheck" is
# never silenced by accident.
_HEALTH_REQUEST_LINE = '"GET /api/health HTTP'


class HealthAccessFilter(logging.Filter):
    """Drop successful `GET /api/health` access lines; keep everything else."""

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if _HEALTH_REQUEST_LINE in msg and " 200" in msg:
            return False
        return True


def log_health_enabled() -> bool:
    return os.getenv("MD_BRIDGE_LOG_HEALTH") == "true"


def install_health_access_filter() -> bool:
    """Attach the health filter to the `uvicorn.access` logger.

    No-ops (and reports False) when `MD_BRIDGE_LOG_HEALTH=true`. Idempotent: a
    second call does not stack a duplicate filter.
    """
    if log_health_enabled():
        return False
    logger = logging.getLogger("uvicorn.access")
    if not any(isinstance(f, HealthAccessFilter) for f in logger.filters):
        logger.addFilter(HealthAccessFilter())
    return True
