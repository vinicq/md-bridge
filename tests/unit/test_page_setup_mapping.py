"""Unit coverage for the markdown-to-pdf page-box mapping (#243).

Pure functions only: no Chromium. Loaded through the md_to_pdf_mod fixture so the
vendored script's import-time stdout rebind is stripped.
"""
from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def mod(md_to_pdf_mod):
    return md_to_pdf_mod


def test_none_preserves_the_historic_pdf_kwargs(mod):
    # The default path must reproduce the old hardcoded call exactly, so existing
    # renders and goldens do not move.
    kw = mod.resolve_pdf_kwargs(None, {})
    assert kw["format"] == "A4"
    assert kw["margin"] == {"top": "2.5cm", "right": "2cm", "bottom": "2.5cm", "left": "2cm"}
    assert kw["print_background"] is True
    assert kw["prefer_css_page_size"] is True
    assert "display_header_footer" not in kw  # no header/footer by default


def test_page_size_maps_through(mod):
    for size in ("A4", "Letter", "Legal"):
        assert mod.resolve_pdf_kwargs({"page_size": size}, {})["format"] == size


def test_unknown_page_size_falls_back_to_a4(mod):
    assert mod.resolve_pdf_kwargs({"page_size": "A3"}, {})["format"] == "A4"


def test_margin_presets(mod):
    assert mod.resolve_pdf_kwargs({"margins": "tight"}, {})["margin"]["top"] == "1.5cm"
    assert mod.resolve_pdf_kwargs({"margins": "loose"}, {})["margin"]["top"] == "3.5cm"
    assert mod.resolve_pdf_kwargs({"margins": "normal"}, {})["margin"]["top"] == "2.5cm"


def test_footer_token_page_and_pages_become_chromium_spans(mod):
    kw = mod.resolve_pdf_kwargs({"footer": {"center": "{{page}} / {{pages}}"}}, {})
    assert kw["display_header_footer"] is True
    assert 'class="pageNumber"' in kw["footer_template"]
    assert 'class="totalPages"' in kw["footer_template"]


def test_title_author_date_substituted_from_front_matter(mod):
    fm = {"title": "My Doc", "author": {"name": "Ada Lovelace"}, "date": "2026-01-02"}
    kw = mod.resolve_pdf_kwargs({"header": {"left": "{{title}}", "right": "{{author}} {{date}}"}}, fm)
    h = kw["header_template"]
    assert "My Doc" in h
    assert "Ada Lovelace" in h
    assert "2026-01-02" in h


def test_date_token_without_front_matter_is_empty_not_the_clock(mod):
    # The print clock must never leak in: {{date}} with no front-matter date
    # renders empty, and the native print-date class is never emitted.
    kw = mod.resolve_pdf_kwargs({"footer": {"center": "{{date}}"}}, {})
    assert 'class="date"' not in kw["footer_template"]
    assert 'class="title"' not in kw["footer_template"]
    assert 'class="url"' not in kw["footer_template"]


def test_running_content_clamps_a_tight_margin_so_it_is_not_clipped(mod):
    # tight = 1.5cm already at the floor; a 1.0cm would be raised. Verify a header
    # forces top >= 1.5cm even when the preset would be smaller is moot for the
    # presets, so assert the floor holds for tight + header.
    kw = mod.resolve_pdf_kwargs({"margins": "tight", "header": {"center": "{{page}}"}}, {})
    assert float(kw["margin"]["top"].rstrip("cm")) >= 1.5


def test_empty_slots_emit_no_header_footer(mod):
    kw = mod.resolve_pdf_kwargs({"header": {"left": "", "center": "", "right": ""}}, {})
    assert "display_header_footer" not in kw


def test_build_running_template_returns_none_when_all_slots_empty(mod):
    assert mod.build_running_template({"left": "", "center": "", "right": ""}, {}) is None


def test_no_template_css_carries_a_dead_at_page_rule():
    # Chromium ignores @page margins / margin-boxes, so a stray @page rule is a
    # silent no-op. Keep the templates free of it (the dead block was removed in
    # #243); this guards against it creeping back.
    import re
    from pathlib import Path

    templates = Path(__file__).resolve().parents[2] / "packages" / "markdown-to-pdf" / "templates"
    offenders = []
    for p in templates.glob("*.css"):
        # Strip /* ... */ comments first; the theme files legitimately mention
        # @page in prose explaining why it is avoided.
        code = re.sub(r"/\*.*?\*/", "", p.read_text(encoding="utf-8"), flags=re.DOTALL)
        if "@page" in code:
            offenders.append(p.name)
    assert offenders == [], f"@page is inert under Chromium; remove it from {offenders}"
