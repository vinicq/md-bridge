"""Dump the app's OpenAPI schema as JSON to stdout.

The web app's `gen:api` npm script pipes this into a committed
`apps/web/src/lib/openapi.json` snapshot, which `openapi-typescript` turns
into typed request/response definitions. Running it needs no server and makes
no network call: it builds the app in-process and serializes `app.openapi()`.

Keys are sorted so the output is byte-stable across runs, which is what the
CI drift check diffs against.

Usage: python -m app.export_openapi > apps/web/src/lib/openapi.json
"""
from __future__ import annotations

import json
import sys

from app.main import app


def main() -> None:
    json.dump(app.openapi(), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
