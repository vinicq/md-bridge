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


class MdToPdfOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lang: SupportedLang = "pt-BR"


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
