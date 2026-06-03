"""Unit coverage for the format-pair registry (#60). Pure, no HTTP."""
from __future__ import annotations

import pytest
from app.services import formats


def test_registry_exposes_the_shipped_pairs():
    slugs = {f.slug for f in formats.list_formats()}
    assert {"pdf-to-md", "md-to-pdf", "md-to-docx"} <= slugs


def test_shipped_pairs_carry_an_endpoint_planned_ones_do_not():
    for f in formats.list_formats():
        if f.status == "shipped":
            assert f.endpoint and f.endpoint.startswith("/api/"), f.slug
        else:
            assert f.endpoint is None, f.slug


def test_get_format_returns_metadata():
    f = formats.get_format("md-to-docx")
    assert f.label == "Markdown → DOCX"
    assert f.source == "md" and f.target == "docx"
    assert f.output_mime.endswith("wordprocessingml.document")
    assert f.endpoint == "/api/md-to-docx"


def test_unknown_slug_raises_unknown_format():
    with pytest.raises(formats.UnknownFormatError) as exc:
        formats.get_format("nope-to-zip")
    assert exc.value.status_code == 400
    assert exc.value.code == "unknown_format"
    assert exc.value.slug == "nope-to-zip"


def test_to_dict_round_trips_the_public_fields():
    d = formats.get_format("md-to-docx").to_dict()
    assert set(d) == {
        "slug",
        "label",
        "source",
        "target",
        "input_mime",
        "output_mime",
        "status",
        "endpoint",
    }
    assert d["status"] == "shipped"
