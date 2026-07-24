"""Unit coverage for the LLM document-parser contract (#457).

No network here: selection, payload/cleanup, typed errors, the redirect refusal,
and the no-secret-leak guarantee are exercised through the real resolver and a
monkeypatched `_post_json`. The live HTTP path is covered in the integration
tier with an in-process stub.
"""
from __future__ import annotations

import pytest
from app.errors import ApiError
from app.services import document_parser as dp


def _one_page_pdf() -> bytes:
    import pymupdf

    doc = pymupdf.open()
    try:
        doc.new_page(width=200, height=200)
        return doc.tobytes()
    finally:
        doc.close()


def test_selector_is_none_when_unset_or_traditional(monkeypatch):
    monkeypatch.delenv("MD_BRIDGE_OCR_PROVIDER", raising=False)
    assert dp.selected_document_parser() is None
    monkeypatch.setenv("MD_BRIDGE_OCR_PROVIDER", "tesseract")
    assert dp.selected_document_parser() is None


def test_selector_returns_custom_parser(monkeypatch):
    monkeypatch.setenv("MD_BRIDGE_OCR_PROVIDER", "custom")
    parser = dp.selected_document_parser()
    assert isinstance(parser, dp.OpenAiCompatibleParser)
    assert parser.name == "custom"


def test_available_reflects_url_configured(monkeypatch):
    parser = dp.OpenAiCompatibleParser("custom")
    monkeypatch.delenv("MD_BRIDGE_OCR_CUSTOM_URL", raising=False)
    assert parser.available() is False
    monkeypatch.setenv("MD_BRIDGE_OCR_CUSTOM_URL", "http://ocr:8000/v1")
    assert parser.available() is True


def test_clean_markdown_strips_grounding_tokens():
    raw = "<|det|>[[1,2]]<|/det|><|ref|>Title<|/ref|>\n<|ref|>Body<|/ref|>"
    assert dp._clean_markdown(raw) == "Title\nBody"
    # No grounding tokens: returned as-is (trimmed).
    assert dp._clean_markdown("  # Plain\n") == "# Plain"


def test_parse_builds_markdown_and_carries_no_secret(monkeypatch):
    monkeypatch.setenv("MD_BRIDGE_OCR_CUSTOM_URL", "http://ocr:8000/v1")
    monkeypatch.setenv("MD_BRIDGE_OCR_CUSTOM_MODEL", "some/model")
    monkeypatch.setenv("MD_BRIDGE_OCR_CUSTOM_KEY", "secret-token")

    seen: dict = {}

    def _fake_post(url, payload, *, key):
        seen["url"] = url
        seen["key"] = key
        seen["model"] = payload["model"]
        return {"choices": [{"message": {"content": "# Page"}}]}

    monkeypatch.setattr(dp, "_post_json", _fake_post)
    result = dp.OpenAiCompatibleParser("custom").parse(_one_page_pdf(), page_break=False)

    assert seen["url"] == "http://ocr:8000/v1/chat/completions"
    assert seen["key"] == "secret-token"
    assert seen["model"] == "some/model"
    assert result.md == "# Page"
    assert result.provider == "custom"
    assert result.duration_ms >= 0
    # The result must not expose the endpoint or the key.
    assert not hasattr(result, "url")
    assert not hasattr(result, "key")
    assert "secret-token" not in repr(result)


def test_missing_url_or_model_raises_typed_503(monkeypatch):
    monkeypatch.delenv("MD_BRIDGE_OCR_CUSTOM_URL", raising=False)
    with pytest.raises(ApiError) as exc:
        dp.OpenAiCompatibleParser("custom").parse(_one_page_pdf(), page_break=False)
    assert exc.value.status_code == 503
    assert exc.value.code == "ocr_provider_unavailable"

    monkeypatch.setenv("MD_BRIDGE_OCR_CUSTOM_URL", "http://ocr:8000/v1")
    monkeypatch.delenv("MD_BRIDGE_OCR_CUSTOM_MODEL", raising=False)
    with pytest.raises(ApiError) as exc:
        dp.OpenAiCompatibleParser("custom").parse(_one_page_pdf(), page_break=False)
    assert exc.value.code == "ocr_provider_unavailable"


def test_empty_model_output_raises_502(monkeypatch):
    monkeypatch.setenv("MD_BRIDGE_OCR_CUSTOM_URL", "http://ocr:8000/v1")
    monkeypatch.setenv("MD_BRIDGE_OCR_CUSTOM_MODEL", "some/model")
    monkeypatch.setattr(dp, "_post_json", lambda *a, **k: {"choices": [{"message": {"content": "  "}}]})
    with pytest.raises(ApiError) as exc:
        dp.OpenAiCompatibleParser("custom").parse(_one_page_pdf(), page_break=False)
    assert exc.value.status_code == 502
    assert exc.value.code == "ocr_failed"


def test_redirect_is_refused():
    handler = dp._NoRedirect()
    with pytest.raises(ApiError) as exc:
        handler.redirect_request(None, None, 302, "Found", {}, "http://evil.example/steal")
    assert exc.value.status_code == 502
    assert exc.value.code == "ocr_failed"


def test_parser_over_cap_returns_413_before_any_call(monkeypatch):
    # A parser-selected scan over MD_BRIDGE_OCR_MAX_PAGES is rejected with 413
    # before the model is called, mirroring the tesseract cap. Stub the inspector
    # so no real multi-page scan is needed; _post_json is never reached.
    from app.schemas.convert import InspectPdfResponse
    from app.services import pdf_to_md

    monkeypatch.setenv("MD_BRIDGE_OCR_PROVIDER", "custom")
    monkeypatch.setenv("MD_BRIDGE_OCR_CUSTOM_URL", "http://ocr:8000/v1")
    monkeypatch.setenv("MD_BRIDGE_OCR_CUSTOM_MODEL", "some/model")
    monkeypatch.setenv("MD_BRIDGE_OCR_MAX_PAGES", "1")
    monkeypatch.setattr(
        pdf_to_md,
        "inspect_pdf_bytes",
        lambda _b, _f: InspectPdfResponse(
            pages=5, body_size_pt=0.0, heading_sizes_pt=[], fonts=[], tagged=False, needs_ocr=True
        ),
    )

    with pytest.raises(ApiError) as exc:
        pdf_to_md.convert_pdf_bytes(b"%PDF-1.4 stub", filename="scan.pdf")
    assert exc.value.status_code == 413
    assert exc.value.code == "ocr_too_many_pages"
