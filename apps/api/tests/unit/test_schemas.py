"""Pure-function tests of the pydantic schemas. No I/O, no app, no HTTP."""
from __future__ import annotations

import pytest
from app.schemas.convert import (
    ConvertStats,
    FrontMatter,
    InspectPdfResponse,
    MdToPdfOptions,
    PdfToMdOptions,
    PdfToMdResponse,
)
from pydantic import ValidationError


def test_pdf_to_md_options_defaults():
    opts = PdfToMdOptions()
    assert opts.page_break is False
    assert opts.with_images is False
    assert opts.front_matter is True
    assert opts.detect_blockquotes is False
    assert opts.cluster_headings is False
    assert opts.subtract_running_furniture is False
    assert opts.allow_html == frozenset()
    assert opts.preserve_line_breaks is False
    assert opts.max_heading_level == 3
    assert opts.footnote_pairing is False
    assert opts.lang == "pt-BR"


def test_md_to_pdf_options_theme_defaults_to_default():
    from app.schemas.convert import MdToPdfOptions

    assert MdToPdfOptions().theme == "default"


def test_pdf_to_md_options_max_heading_level_range():
    assert PdfToMdOptions(max_heading_level=6).max_heading_level == 6
    with pytest.raises(ValidationError):
        PdfToMdOptions(max_heading_level=7)
    with pytest.raises(ValidationError):
        PdfToMdOptions(max_heading_level=0)


def test_pdf_to_md_options_allow_html_accepts_capped_tag():
    opts = PdfToMdOptions(allow_html={"sup"})
    assert opts.allow_html == frozenset({"sup"})


def test_pdf_to_md_options_allow_html_rejects_dangerous_tag():
    with pytest.raises(ValidationError):
        PdfToMdOptions(allow_html={"script"})


def test_pdf_to_md_options_rejects_unknown_field():
    with pytest.raises(ValidationError):
        PdfToMdOptions.model_validate({"page_break": True, "rogue": "x"})


def test_pdf_to_md_options_rejects_non_bool():
    # Pydantic v2 accepts "yes"/"no" strings as booleans by default; ensure
    # a clearly non-coercible value (a list) is rejected.
    with pytest.raises(ValidationError):
        PdfToMdOptions.model_validate({"page_break": [1, 2, 3]})


def test_md_to_pdf_options_defaults():
    opts = MdToPdfOptions()
    assert opts.lang == "pt-BR"


def test_md_to_pdf_options_rejects_unknown_field():
    # `theme` is now a real field (#23); use a genuinely unknown key to keep
    # asserting the extra="forbid" guard.
    with pytest.raises(ValidationError):
        MdToPdfOptions.model_validate({"no_such_option": "editorial"})


def test_pdf_to_md_options_panel_payload_round_trips():
    # The exact options shape the web OptionsPanel forwards (#59). Locks the
    # frontend <-> schema contract: every exposed field is accepted together.
    payload = {
        "front_matter": False,
        "page_break": True,
        "with_images": True,
        "detect_blockquotes": True,
        "cluster_headings": True,
        "preserve_line_breaks": True,
        "footnote_pairing": True,
        "max_heading_level": 4,
    }
    opts = PdfToMdOptions.model_validate(payload)
    assert opts.front_matter is False
    assert opts.cluster_headings is True
    assert opts.max_heading_level == 4


def test_pdf_to_md_response_default_collections():
    resp = PdfToMdResponse(md="# hi")
    assert resp.front_matter == FrontMatter()
    assert resp.warnings == []
    assert resp.stats == ConvertStats()


def test_convert_stats_zero_default():
    stats = ConvertStats()
    assert stats.headings == 0
    assert stats.tables == 0
    assert stats.bullets == 0


def test_inspect_pdf_response_round_trips():
    payload = {
        "pages": 4,
        "body_size_pt": 11.0,
        "heading_sizes_pt": [18.0, 14.0],
        "fonts": [{"name": "Body", "size": 11.0, "count": 100, "sample": "Hello"}],
        "tagged": True,
        "needs_ocr": False,
    }
    parsed = InspectPdfResponse.model_validate(payload)
    assert parsed.pages == 4
    assert parsed.fonts[0].name == "Body"
