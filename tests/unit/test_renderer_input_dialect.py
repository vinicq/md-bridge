"""Renderer input-dialect locks: setext headings (#177) and HTML comment
passthrough (#160).

These behaviors are already provided by python-markdown with the renderer's
extension set, but nothing pinned them. A future change to MD_EXTENSIONS could
silently drop either one. These pure unit checks run the exact same markdown
config the renderer uses (md_to_pdf_mod.MD_EXTENSIONS), no Chromium, so they
catch a regression at the HTML stage. The end-to-end PDF behavior is locked in
apps/api/tests/integration/test_md_to_pdf.py.
"""
from __future__ import annotations

import markdown
import pytest


@pytest.fixture(scope="module")
def md_extensions(md_to_pdf_mod):
    # The same extension list the renderer feeds to markdown.markdown.
    return md_to_pdf_mod.MD_EXTENSIONS


def _html(src: str, exts) -> str:
    return markdown.markdown(src, extensions=exts, output_format="html5")


def test_setext_headings_become_h1_and_h2(md_extensions):
    # An underlined heading (=== for H1, --- for H2) is valid CommonMark input;
    # the renderer must treat it as a heading, not literal text (#177).
    html = _html("Setext H1\n=========\n\nSetext H2\n---------\n\nBody paragraph.", md_extensions)
    assert "<h1" in html and ">Setext H1</h1>" in html, html
    assert "<h2" in html and ">Setext H2</h2>" in html, html


def test_html_comment_passes_through_between_paragraphs(md_extensions):
    # HTML comments are an in-source notes idiom; they must survive to the HTML
    # output (browsers and the PDF renderer ignore them visually) rather than
    # being stripped or escaped into visible text (#160).
    html = _html("Para A.\n\n<!-- hidden build note -->\n\nPara B.", md_extensions)
    assert "<!-- hidden build note -->" in html, html
    assert "<p>Para A.</p>" in html and "<p>Para B.</p>" in html, html
