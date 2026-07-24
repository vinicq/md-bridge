"""Interchangeable LLM document parsers for scanned PDFs (#457).

A DocumentParserProvider turns rendered PDF pages into Markdown by calling an
OpenAI-compatible `/chat/completions` endpoint the operator hosts. This is the
LLM counterpart to the traditional OcrProvider contract (#441): OcrProvider
produces a searchable PDF that the deterministic converter then reads, while a
DocumentParserProvider returns Markdown directly. The two never share output.

Everything here is opt-in and inert until the operator points
`MD_BRIDGE_OCR_PROVIDER` at a parser AND configures its endpoint URL. The lean
install ships no parser, a native PDF with a text layer never reaches this code,
and a no-LLM install converts exactly as before. Endpoint URLs and API keys are
read only here, server-side, and never appear in a response, a log, or the
OpenAPI schema.

PR-1 ships the generic `custom` provider (fully env-configured). The named
`unlimited` and `deepseek` recipes land as registry data in a follow-up; nothing
here privileges a specific third-party model.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

import pymupdf

from app.errors import ApiError

# Grounding tokens some vision-OCR models emit around their output. Stripped
# before the Markdown is returned so internal markers never reach the document.
_REF_RE = re.compile(r"<\|ref\|>(.*?)<\|/ref\|>", re.DOTALL)
_DET_RE = re.compile(r"<\|det\|>.*?<\|/det\|>", re.DOTALL)

_DEFAULT_TIMEOUT = 600
_DEFAULT_PROMPT = "Convert this document page to Markdown. Preserve headings, lists, and tables."


@dataclass(frozen=True)
class ParseResult:
    """Output of a DocumentParserProvider. Carries the Markdown plus provider
    metadata, never the endpoint URL, the API key, or a filename, so surfacing
    it cannot leak a secret or document identity."""

    md: str
    provider: str
    duration_ms: int
    warnings: list[str] = field(default_factory=list)


class DocumentParserProvider(Protocol):
    name: str

    def available(self) -> bool:
        """True when this provider's endpoint URL is configured."""

    def parse(self, pdf_bytes: bytes, *, page_break: bool) -> ParseResult:
        """Render each page and return the model's Markdown."""


def _timeout() -> int:
    raw = os.getenv("MD_BRIDGE_OCR_LLM_TIMEOUT", "").strip()
    if not raw:
        return _DEFAULT_TIMEOUT
    try:
        value = int(raw)
    except ValueError:
        return _DEFAULT_TIMEOUT
    return value if value > 0 else _DEFAULT_TIMEOUT


class _NoRedirect(HTTPRedirectHandler):
    """Refuse any 3xx. A redirect is a silent host switch that could forward the
    request and its API key to an address the operator did not configure."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise ApiError(
            502,
            "ocr_failed",
            "The OCR endpoint attempted a redirect, which is refused.",
        )


def _post_json(url: str, payload: dict, *, key: str) -> dict:
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if key:
        # Authorization: Bearer <key>, read server-side only. A configurable
        # header name is deferred until a non-Bearer gateway is a real need.
        headers["Authorization"] = f"Bearer {key}"
    request = Request(url, data=body, headers=headers, method="POST")
    opener = build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=_timeout()) as response:  # noqa: S310 - operator-configured URL
            return json.loads(response.read())
    except HTTPError as exc:
        raise ApiError(502, "ocr_failed", f"OCR service returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ApiError(503, "ocr_unavailable", "OCR service is unavailable.") from exc
    except json.JSONDecodeError as exc:
        raise ApiError(502, "ocr_failed", "OCR service returned invalid JSON.") from exc


def _clean_markdown(text: str) -> str:
    text = _DET_RE.sub("", text)
    references = _REF_RE.findall(text)
    if references:
        cleaned = "\n".join(ref.strip() for ref in references if ref.strip())
        if cleaned:
            return cleaned
    return text.strip()


class OpenAiCompatibleParser:
    """A document parser backed by an OpenAI-compatible chat endpoint.

    All connection details come from the environment under the provider's own
    namespace, so nothing is baked into the code:

    - `MD_BRIDGE_OCR_<NAME>_URL`   (required) the base URL, e.g. http://ocr:8000/v1
    - `MD_BRIDGE_OCR_<NAME>_MODEL` (required) the model name to request
    - `MD_BRIDGE_OCR_<NAME>_KEY`   (optional) the API key, sent as Bearer auth
    - `MD_BRIDGE_OCR_<NAME>_PROMPT` (optional) the per-page instruction
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def _env(self, knob: str) -> str:
        return os.getenv(f"MD_BRIDGE_OCR_{self.name.upper()}_{knob}", "").strip()

    def available(self) -> bool:
        return bool(self._env("URL"))

    def _require(self, knob: str) -> str:
        value = self._env(knob)
        if not value:
            raise ApiError(
                503,
                "ocr_provider_unavailable",
                f"OCR provider {self.name!r} is selected but "
                f"MD_BRIDGE_OCR_{self.name.upper()}_{knob} is not set.",
            )
        return value

    def _payload(self, model: str, prompt: str, image: bytes) -> dict:
        data_url = "data:image/png;base64," + base64.b64encode(image).decode("ascii")
        return {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            "temperature": 0.0,
            "max_tokens": 8192,
        }

    def parse(self, pdf_bytes: bytes, *, page_break: bool) -> ParseResult:
        start = time.monotonic()
        endpoint = self._require("URL").rstrip("/") + "/chat/completions"
        model = self._require("MODEL")
        prompt = self._env("PROMPT") or _DEFAULT_PROMPT
        key = self._env("KEY")

        document = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        pages: list[str] = []
        try:
            for page_number, page in enumerate(document, start=1):
                image = page.get_pixmap(dpi=300, alpha=False).tobytes("png")
                response = _post_json(endpoint, self._payload(model, prompt, image), key=key)
                content = self._content(response, page_number)
                pages.append(_clean_markdown(content))
        finally:
            document.close()

        separator = "\n\n---\n\n" if page_break else "\n\n"
        duration_ms = int((time.monotonic() - start) * 1000)
        return ParseResult(
            md=separator.join(pages), provider=self.name, duration_ms=duration_ms, warnings=[]
        )

    @staticmethod
    def _content(response: dict, page_number: int) -> str:
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ApiError(
                502, "ocr_failed", f"OCR service returned no Markdown for page {page_number}."
            ) from exc
        if not isinstance(content, str) or not content.strip():
            raise ApiError(
                502, "ocr_failed", f"OCR service returned empty Markdown for page {page_number}."
            )
        return content


# Registry of LLM document parsers. PR-1 ships only the generic operator
# configured `custom` provider; the named recipes (unlimited, deepseek) land as
# data in a follow-up, each resolving to the same OpenAI-compatible adapter.
_PARSERS: dict[str, type] = {"custom": OpenAiCompatibleParser}


def selected_document_parser() -> DocumentParserProvider | None:
    """Return the DocumentParserProvider selected by MD_BRIDGE_OCR_PROVIDER, or
    None when the selector is unset or names a traditional OCR provider.

    None means the caller keeps its existing (tesseract / searchable-PDF) path,
    so this is inert until an operator opts in explicitly."""
    name = os.getenv("MD_BRIDGE_OCR_PROVIDER", "").strip()
    factory = _PARSERS.get(name)
    if factory is None:
        return None
    return factory(name)
