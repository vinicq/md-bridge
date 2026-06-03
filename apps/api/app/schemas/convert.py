"""Pydantic schemas for the conversion endpoints."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SupportedLang = Literal["pt-BR", "en", "es", "de", "fr", "it"]

# Inline, semantic, non-scripting tags the converter may ever emit (#154).
# Kept identical to ALLOWED_HTML_TAGS in the vendored converter; a test asserts
# they match. Everything else (script/style/iframe/a/img/...) is rejected here
# so an opt-in HTML policy can never become a script-injection vector.
ALLOWED_HTML_TAGS = frozenset({"sup", "sub", "small", "kbd", "abbr"})


class PdfToMdOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_break: bool = False
    with_images: bool = False
    front_matter: bool = True
    detect_blockquotes: bool = False
    cluster_headings: bool = False
    subtract_running_furniture: bool = False
    allow_html: frozenset[str] = frozenset()
    preserve_line_breaks: bool = False
    max_heading_level: int = Field(default=3, ge=1, le=6)
    footnote_pairing: bool = False
    lang: SupportedLang = "pt-BR"

    @field_validator("allow_html")
    @classmethod
    def _cap_allow_html(cls, v: frozenset[str]) -> frozenset[str]:
        bad = v - ALLOWED_HTML_TAGS
        if bad:
            raise ValueError(
                f"allow_html may only contain {sorted(ALLOWED_HTML_TAGS)}; "
                f"rejected: {sorted(bad)}"
            )
        return v


class RunningContent(BaseModel):
    """Header or footer text for the three margin-box slots (#243).

    Each slot accepts plain text plus the tokens {{title}}, {{author}}, {{date}}
    (substituted from front matter, never the print clock) and {{page}},
    {{pages}} (filled by the renderer). Empty slots render nothing.
    """

    model_config = ConfigDict(extra="forbid")

    left: str = ""
    center: str = ""
    right: str = ""


class PageSetupOptions(BaseModel):
    """Per-request page geometry and running content for Markdown -> PDF (#243)."""

    model_config = ConfigDict(extra="forbid")

    page_size: Literal["A4", "Letter", "Legal"] = "A4"
    margins: Literal["tight", "normal", "loose"] = "normal"
    header: RunningContent | None = None
    footer: RunningContent | None = None


class MdToPdfOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Theme slug selecting which stylesheet the renderer stacks (#23). Defaults
    # to "default"; an unknown slug is rejected at the service with 400
    # unknown_theme. Validity is checked against the live registry rather than a
    # static enum so a newly added template needs no schema change.
    theme: str = "default"
    lang: SupportedLang = "pt-BR"
    # Page geometry + running header/footer (#243). `None` preserves the historic
    # output exactly: A4, 2.5/2/2.5/2 cm margins, no header/footer.
    page_setup: PageSetupOptions | None = None


class MdToDocxOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # The DOCX converter takes no tunables yet; the options envelope is kept for
    # parity with the other pairs and so future fields are non-breaking.
    lang: SupportedLang = "pt-BR"


class ThemeInfo(BaseModel):
    slug: str
    name: str
    description: str
    family: str


class FormatInfo(BaseModel):
    slug: str
    label: str
    source: str
    target: str
    input_mime: str
    output_mime: str
    status: str
    endpoint: str | None = None


class FrontMatter(BaseModel):
    title: str | None = None
    author: str | None = None
    date: str | None = None
    source: str | None = None
    pages: int | None = None


class ConvertStats(BaseModel):
    headings: int = 0
    tables: int = 0
    bullets: int = 0


class PdfToMdResponse(BaseModel):
    md: str
    front_matter: FrontMatter = Field(default_factory=FrontMatter)
    warnings: list[str] = Field(default_factory=list)
    stats: ConvertStats = Field(default_factory=ConvertStats)
    ocr_applied: bool = False


class FontUsage(BaseModel):
    name: str
    size: float
    count: int
    sample: str


class InspectPdfResponse(BaseModel):
    pages: int
    body_size_pt: float
    heading_sizes_pt: list[float]
    fonts: list[FontUsage]
    tagged: bool
    needs_ocr: bool
