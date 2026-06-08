"""Sweeps test-time artifacts off disk.

Pytest collects test files alphabetically. The `zzz` prefix keeps this module
at the very end of the run, so it sees every leftover the suite might have
created: tempdirs from the service helpers, coverage shards, pycache trees.
The test passes when nothing remains.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

PREFIXES = (
    "md-bridge-pdf2md-",
    "md-bridge-md2pdf-",
    "md-bridge-inspect-",
    "regress-pdf2md-",
    "regress-md2pdf-",
    "regress-istqb-",
)


def _project_root() -> Path:
    # apps/api/tests/integration/test_zzz_cleanup.py -> parents[4] is the repo root
    return Path(__file__).resolve().parents[4]


def test_zzz_cleanup_tempdirs():
    tmp_root = Path(tempfile.gettempdir())
    leaked: list[Path] = []
    for prefix in PREFIXES:
        for p in tmp_root.glob(f"{prefix}*"):
            try:
                if p.is_dir():
                    shutil.rmtree(p, ignore_errors=True)
                elif p.exists():
                    p.unlink(missing_ok=True)
                if p.exists():
                    leaked.append(p)
            except OSError:
                leaked.append(p)
    assert not leaked, f"could not remove: {leaked}"


def test_zzz_cleanup_project_artifacts():  # falsegreen: ignore[C2b]
    root = _project_root()
    targets = [
        root / "apps" / "api" / ".coverage",
        root / ".coverage",
        root / "apps" / "api" / "htmlcov",
        root / "htmlcov",
        root / "apps" / "api" / "md_bridge_api.egg-info",
    ]
    for t in targets:
        if t.is_dir():
            shutil.rmtree(t, ignore_errors=True)
        elif t.exists():
            t.unlink(missing_ok=True)
    # No assertion: cleanup is best-effort. The point is the side effect.
