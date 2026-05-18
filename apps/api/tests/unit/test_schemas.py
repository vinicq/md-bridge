"""Pure-function tests of the pydantic schemas. No I/O, no app, no HTTP."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.convert import (
    ConvertStats,
    FrontMatter,
    InspectPdfResponse,
    MdToPdfOptions,
    PdfToMdOptions,
    PdfToMdResponse,
    Theme,
)


def test_pdf_to_md_options_defaults():
    opts = PdfToMdOptions()
    assert opts.page_break is False
    assert opts.with_images is False
    assert opts.front_matter is True
    assert opts.lang == "pt-BR"


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
    assert opts.theme == "default"


def test_md_to_pdf_options_accepts_arbitrary_theme_id():
    # Theme validation is the route's job; the schema lets any string through
    # because new themes get dropped into the templates folder at runtime.
    opts = MdToPdfOptions.model_validate({"theme": "editorial"})
    assert opts.theme == "editorial"


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


def test_theme_optional_preview():
    t = Theme(id="default", name="Default A4")
    assert t.preview_url is None
