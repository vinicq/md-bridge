"""Unit coverage for the OCR page-count cap (#208).

The cap short-circuits the 300-DPI OCR pre-pass before it runs. These tests
stub the inspector and the OCR call (unit tier, mocks allowed) so the guard
logic is verified on every platform without a real Tesseract or PDF.
"""
from __future__ import annotations

import pytest
from app.errors import ApiError
from app.schemas.convert import InspectPdfResponse
from app.services import pdf_to_md
from app.services.ocr import DEFAULT_OCR_MAX_PAGES, get_max_pages


@pytest.mark.parametrize(
    "raw, expected",
    [
        (None, 0),
        ("", 0),
        ("   ", 0),
        ("0", 0),
        ("-5", 0),
        ("abc", 0),
        ("50", 50),
        (" 12 ", 12),
    ],
)
def test_get_max_pages_reads_env_boundary(monkeypatch, raw, expected):
    if raw is None:
        monkeypatch.delenv("MD_BRIDGE_OCR_MAX_PAGES", raising=False)
    else:
        monkeypatch.setenv("MD_BRIDGE_OCR_MAX_PAGES", raw)
    assert get_max_pages() == expected


def test_default_is_no_cap():
    assert DEFAULT_OCR_MAX_PAGES == 0


def _stub_inspect(pages: int):
    def _inner(pdf_bytes: bytes, filename: str) -> InspectPdfResponse:
        return InspectPdfResponse(
            pages=pages,
            body_size_pt=0.0,
            heading_sizes_pt=[],
            fonts=[],
            tagged=False,
            needs_ocr=True,
        )

    return _inner


@pytest.fixture
def ocr_enabled_no_binary(monkeypatch):
    """Force the OCR branch on and make the real OCR call fail. A blocked scan
    raises `ocr_too_many_pages` (413); a scan that clears the cap reaches this
    call and surfaces as `ocr_failed` (500), so the two codes tell the guard's
    two paths apart."""
    monkeypatch.setattr(pdf_to_md, "ocr_enabled", lambda: True)

    def _boom(*_args, **_kwargs):
        raise RuntimeError("no tesseract in unit tier")

    monkeypatch.setattr(pdf_to_md, "ocr_pdf_bytes", _boom)


def test_scan_over_cap_is_rejected_before_ocr(monkeypatch, ocr_enabled_no_binary):
    monkeypatch.setenv("MD_BRIDGE_OCR_MAX_PAGES", "3")
    monkeypatch.setattr(pdf_to_md, "inspect_pdf_bytes", _stub_inspect(pages=10))

    with pytest.raises(ApiError) as exc:
        pdf_to_md.convert_pdf_bytes(b"%PDF-1.4 stub", filename="scan.pdf")

    assert exc.value.status_code == 413
    assert exc.value.code == "ocr_too_many_pages"
    assert exc.value.extra_detail == {"pages": 10, "max_pages": 3}


def test_scan_at_cap_passes_the_guard(monkeypatch, ocr_enabled_no_binary):
    # pages == cap is within budget; control reaches the OCR call (ocr_failed),
    # not the cap rejection (ocr_too_many_pages).
    monkeypatch.setenv("MD_BRIDGE_OCR_MAX_PAGES", "3")
    monkeypatch.setattr(pdf_to_md, "inspect_pdf_bytes", _stub_inspect(pages=3))

    with pytest.raises(ApiError) as exc:
        pdf_to_md.convert_pdf_bytes(b"%PDF-1.4 stub", filename="scan.pdf")
    assert exc.value.code == "ocr_failed"


def test_cap_disabled_never_blocks(monkeypatch, ocr_enabled_no_binary):
    monkeypatch.delenv("MD_BRIDGE_OCR_MAX_PAGES", raising=False)
    monkeypatch.setattr(pdf_to_md, "inspect_pdf_bytes", _stub_inspect(pages=9999))

    # Default (no cap) lets any length through to OCR (ocr_failed, not the cap).
    with pytest.raises(ApiError) as exc:
        pdf_to_md.convert_pdf_bytes(b"%PDF-1.4 stub", filename="scan.pdf")
    assert exc.value.code == "ocr_failed"


def test_force_over_cap_skips_ocr_and_converts(monkeypatch, ocr_enabled_no_binary):
    # force=True is the documented "convert anyway" escape hatch. Over the cap it
    # must skip OCR (ocr_pdf_bytes is stubbed to raise, so any call fails the
    # test) and fall through to a raw conversion instead of returning 413.
    monkeypatch.setenv("MD_BRIDGE_OCR_MAX_PAGES", "1")
    monkeypatch.setattr(pdf_to_md, "inspect_pdf_bytes", _stub_inspect(pages=5))

    class _StubMod:
        def convert_document(self, pdf_path, md_path, **_kw):
            md_path.write_text("# forced\n\nbody\n", encoding="utf-8")

    monkeypatch.setattr(pdf_to_md, "pdf_to_md_module", lambda: _StubMod())

    result = pdf_to_md.convert_pdf_bytes(
        b"%PDF-1.4 stub", filename="forced.pdf", force=True
    )
    assert result.ocr_applied is False
