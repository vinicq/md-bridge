"""Visual regression for the Markdown -> PDF themes (#245).

The structural md-to-pdf regression only checks the `%PDF-` magic and size, so a
theme's colour, heading numbering, or table styling can regress without any test
going red. This gate rasterizes the committed reference renders under
`docs/design/themes/` and diffs each against a committed PNG baseline.

Why the committed PDFs and not a live render: every reference PDF embeds (subsets)
its fonts, so PyMuPDF rasterizes identical glyphs on any platform and the pixel
diff is stable across Windows dev and Linux CI. When a theme stylesheet changes,
the author regenerates the reference PDF (see docs/design/themes/README.md); this
diff then fails against the old baseline until the baseline is refreshed, forcing
a visible before/after rather than a silent drift.

Regenerate the baselines after an intended theme change:
    python -m pytest tests/regression/test_theme_visual_regression.py --update-golden
"""
from __future__ import annotations

from pathlib import Path

import fitz
import pytest

ROOT = Path(__file__).resolve().parents[2]
THEME_PDFS = ROOT / "docs" / "design" / "themes"
BASELINES = Path(__file__).resolve().parent / "baselines" / "themes"

THEMES = ["default", "academic", "business", "minimal"]

# Render DPI for the comparison. Fixed so the pixel grid is stable.
DPI = 100
# A pixel counts as different when any RGB channel differs by more than this
# (0-255). Absorbs sub-pixel anti-aliasing noise between PyMuPDF builds.
CHANNEL_TOLERANCE = 24
# The whole page fails when more than this fraction of sampled pixels differ.
# Verified that the committed reference PDFs (embedded fonts) rasterize
# byte-identically under the pinned PyMuPDF on both Windows and the Linux CI, so
# normal runs take the byte-equal fast path and never reach this threshold. It
# is a safety net for a future PyMuPDF anti-aliasing shift; a real
# colour/numbering/table regression moves far more (distinct themes differ ~3.8%
# on this sample). A version bump that drifts past this is the maintainer's cue
# to review and regenerate the baselines.
MAX_DIFF_RATIO = 0.005
# Sample every Nth pixel for the tolerant path; dense enough to catch a regional
# change (a recoloured masthead or table header is thousands of pixels), cheap
# enough to stay fast.
SAMPLE_STRIDE = 7


def _render(pdf_path: Path) -> fitz.Pixmap:
    doc = fitz.open(pdf_path)
    try:
        return doc[0].get_pixmap(dpi=DPI, colorspace=fitz.csRGB, alpha=False)
    finally:
        doc.close()


def _diff_ratio(a: fitz.Pixmap, b: fitz.Pixmap) -> float:
    """Fraction of sampled pixels that differ beyond CHANNEL_TOLERANCE."""
    if (a.width, a.height) != (b.width, b.height):
        return 1.0
    sa, sb = a.samples, b.samples
    n = a.width * a.height
    differing = 0
    sampled = 0
    for i in range(0, n, SAMPLE_STRIDE):
        off = i * 3
        sampled += 1
        if (
            abs(sa[off] - sb[off]) > CHANNEL_TOLERANCE
            or abs(sa[off + 1] - sb[off + 1]) > CHANNEL_TOLERANCE
            or abs(sa[off + 2] - sb[off + 2]) > CHANNEL_TOLERANCE
        ):
            differing += 1
    return differing / sampled if sampled else 0.0


@pytest.mark.parametrize("theme", THEMES)
def test_theme_render_matches_baseline(theme: str, update_golden: bool):
    pdf_path = THEME_PDFS / f"{theme}.pdf"
    assert pdf_path.exists(), f"missing reference render: {pdf_path}"

    pix = _render(pdf_path)
    baseline_path = BASELINES / f"{theme}.png"

    if update_golden:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        pix.save(baseline_path)
        pytest.skip(f"updated baseline: {baseline_path.name}")

    assert baseline_path.exists(), (
        f"missing baseline {baseline_path.name}; run with --update-golden to create it"
    )
    baseline = fitz.Pixmap(str(baseline_path))

    # Fast path: identical render (same PyMuPDF build) is byte-equal.
    if pix.samples == baseline.samples:
        return

    ratio = _diff_ratio(pix, baseline)
    assert ratio <= MAX_DIFF_RATIO, (
        f"theme {theme}: rendered PDF differs from baseline by {ratio:.3%} "
        f"(> {MAX_DIFF_RATIO:.1%}). If the change is intentional, regenerate the "
        f"reference PDF and rerun with --update-golden."
    )
