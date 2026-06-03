"""Load the vendored converter scripts as Python modules without modifying them.

The scripts live under `packages/<name>/scripts/` outside this package, so
they are resolved by path via importlib.util and the loaded modules are
cached.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from functools import lru_cache
from pathlib import Path
from types import ModuleType

from app.config import (
    MD_TO_DOCX_SCRIPT,
    MD_TO_PDF_SCRIPT,
    PDF_INSPECT_SCRIPT,
    PDF_TO_MD_SCRIPT,
)

_STDIO_REBIND_RE = re.compile(
    r"^[ \t]*sys\.std(?:out|err)[ \t]*=[ \t]*io\.TextIOWrapper\(sys\.std(?:out|err)\.buffer.*$",
    re.MULTILINE,
)


def _load(name: str, path: Path) -> ModuleType:
    """Import a converter script by path without letting it hijack the host stdout.

    The CLI scripts rebind `sys.stdout` / `sys.stderr` to UTF-8 TextIOWrappers
    at module import time so they print correctly when run from the command
    line on Windows. Inside a server or test process that is fatal: the
    wrapper grabs the buffer of pytest's capture tmpfile and, when the wrapper
    is later garbage-collected, closes that tmpfile. Subsequent capture reads
    then fail with `ValueError: I/O operation on closed file`.

    The source is read, those lines are commented out, compiled, and
    exec_module is called, so the modules import cleanly without touching
    host stdio.
    """
    if not path.exists():
        raise FileNotFoundError(f"Package script not found: {path}")
    source = path.read_text(encoding="utf-8")
    safe_source = _STDIO_REBIND_RE.sub(
        lambda m: "# [stripped by packages_loader] " + m.group(0), source
    )
    code = compile(safe_source, str(path), "exec")
    spec = importlib.util.spec_from_loader(name, loader=None, origin=str(path))
    if spec is None:
        raise ImportError(f"Cannot build import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(code, module.__dict__)
    return module


@lru_cache(maxsize=1)
def pdf_to_md_module() -> ModuleType:
    return _load("md_bridge_pkg_pdf_to_md", PDF_TO_MD_SCRIPT)


@lru_cache(maxsize=1)
def md_to_pdf_module() -> ModuleType:
    return _load("md_bridge_pkg_md_to_pdf", MD_TO_PDF_SCRIPT)


@lru_cache(maxsize=1)
def pdf_inspect_module() -> ModuleType:
    return _load("md_bridge_pkg_pdf_inspect", PDF_INSPECT_SCRIPT)


@lru_cache(maxsize=1)
def md_to_docx_module() -> ModuleType:
    return _load("md_bridge_pkg_md_to_docx", MD_TO_DOCX_SCRIPT)
