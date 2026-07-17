"""Unit coverage for figure anchor id derivation (#165).

Drives `_figure_anchor_id` (pure, no fitz) and confirms the md-to-pdf renderer
attaches the emitted attr-list id to the `<img>`. Tables are out of scope: the
renderer cannot attach an attr-list id to a `<table>`, tracked separately.
"""
from __future__ import annotations

from app.services.packages_loader import md_to_pdf_module, pdf_to_md_module

mod = pdf_to_md_module()
md_mod = md_to_pdf_module()


def test_figure_anchor_id_from_numbered_captions():
    used: set[str] = set()
    assert mod._figure_anchor_id("Figure 3: System architecture", used) == "fig-3"
    assert mod._figure_anchor_id("Fig. 2.1 Results table", used) == "fig-2-1"
    assert mod._figure_anchor_id("Figura 5 - Diagrama de fluxo", used) == "fig-5"


def test_figure_anchor_id_none_without_a_number():
    used: set[str] = set()
    assert mod._figure_anchor_id("Untitled illustration", used) is None
    assert mod._figure_anchor_id("Table 2: not a figure", used) is None


def test_figure_anchor_id_dedupes_repeats():
    used: set[str] = set()
    assert mod._figure_anchor_id("Figure 1", used) == "fig-1"
    assert mod._figure_anchor_id("Figure 1 (duplicate number)", used) == "fig-1-2"
    assert mod._figure_anchor_id("Figure 1 third", used) == "fig-1-3"


def test_renderer_attaches_the_id_to_the_image():
    # The emitted `![alt](p){#fig-3 .figure}` must render to <img id="fig-3">.
    out = md_mod.markdown.markdown(
        "![Arch](a.png){#fig-3 .figure}",
        extensions=md_mod.MD_EXTENSIONS,
        output_format="html5",
    )
    assert 'id="fig-3"' in out
    assert 'class="figure"' in out
