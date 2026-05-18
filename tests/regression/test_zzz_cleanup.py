"""End-of-suite cleanup for the regression layer."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path


def test_zzz_regression_cleanup():
    tmp_root = Path(tempfile.gettempdir())
    for prefix in ("regress-pdf2md-", "regress-md2pdf-", "regress-istqb-"):
        for p in tmp_root.glob(f"{prefix}*"):
            try:
                if p.is_dir():
                    shutil.rmtree(p, ignore_errors=True)
                elif p.exists():
                    p.unlink(missing_ok=True)
            except OSError:
                pass
