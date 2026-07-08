from __future__ import annotations

import shutil

import pymupdf
import pytest
from app.services.ocr import ocr_pdf_bytes

pytest.importorskip("pytesseract")
pytestmark = pytest.mark.skipif(
    shutil.which("tesseract") is None,
    reason="tesseract binary is not installed",
)


def _extract_text(pdf_bytes: bytes) -> str:
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        return "\n".join(page.get_text() for page in doc)


def test_ocr_pdf_bytes_adds_extractable_text(scanned_pdf_bytes: bytes):
    assert not _extract_text(scanned_pdf_bytes).strip()

    ocr_pdf = ocr_pdf_bytes(scanned_pdf_bytes, lang="eng")
    text = _extract_text(ocr_pdf).upper()

    assert "OCR" in text
    assert "BRIDGE" in text


def test_ocr_reads_spanish_with_the_default_language_set(
    scanned_spanish_pdf_bytes: bytes, monkeypatch
):
    # #199: a scanned Spanish document is read with the default multi-language
    # set (no MD_BRIDGE_OCR_LANG), proving Spanish is auto-handled. Needs the
    # spa traineddata installed (CI installs it; skips otherwise).
    from app.services.ocr import get_lang

    monkeypatch.delenv("MD_BRIDGE_OCR_LANG", raising=False)
    lang = get_lang()
    assert "spa" in lang
    assert not _extract_text(scanned_spanish_pdf_bytes).strip()

    ocr_pdf = ocr_pdf_bytes(scanned_spanish_pdf_bytes, lang=lang)
    text = _extract_text(ocr_pdf).upper()

    assert "INFORME" in text
    assert "PRUEBA" in text
    assert "DOCUMENTO" in text


def test_accented_spanish_requires_the_spa_model(
    scanned_accented_spanish_pdf_bytes, monkeypatch
):
    # #204: the accent-free Spanish test above round-trips through `eng` alone, so
    # it never proves `spa` does work. This one does. On a scan-like render of
    # accented Spanish, the default `eng+por+spa` set recovers accented characters
    # (ñ / á / ó / é / í) that the `eng` model drops. The assertion is on the set
    # difference rather than one fixed glyph, so it does not hinge on which accent
    # survives a given render: if `spa` were dropped, both runs would agree and the
    # recovered set would be empty.
    from app.services.ocr import get_lang

    # Clear any MD_BRIDGE_OCR_LANG override so this exercises the built-in default
    # (the thing under test), not a value exported by the environment or leaked by
    # a prior test.
    monkeypatch.delenv("MD_BRIDGE_OCR_LANG", raising=False)
    default_lang = get_lang()
    assert "spa" in default_lang  # guard: we really are testing the default set

    accents = "ñáóéíúü"
    eng_only = _extract_text(
        ocr_pdf_bytes(scanned_accented_spanish_pdf_bytes, lang="eng")
    )
    default = _extract_text(
        ocr_pdf_bytes(scanned_accented_spanish_pdf_bytes, lang=default_lang)
    )

    recovered = {c for c in accents if c in default} - {c for c in accents if c in eng_only}
    assert recovered, (
        "spa should recover accented characters eng drops. "
        f"eng={eng_only!r} default={default!r}"
    )
