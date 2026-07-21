"""Optional Tesseract OCR pre-pass for scanned PDFs."""
from __future__ import annotations

import io
import os
import shutil
from collections import OrderedDict
from hashlib import sha256

import pymupdf

from app.errors import ApiError

_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off"}

# Multi-language Tesseract set so a scanned document is read without an
# operator configuring a per-document language. Tesseract scores each region
# across all three models, which is deterministic given the same input and the
# same installed traineddata. PT-PT and PT-BR share a single `por` model. A
# narrower per-document auto-detect (first-pass language ID) is a follow-up;
# `MD_BRIDGE_OCR_LANG` stays the override escape hatch. (#199)
DEFAULT_OCR_LANG = "eng+por+spa"


def get_lang() -> str:
    return os.getenv("MD_BRIDGE_OCR_LANG", DEFAULT_OCR_LANG)


# OCR rasterizes every page at 300 DPI (see `ocr_pdf_bytes`), so a very long
# scan is a memory/time bomb on a shared or hosted deployment. The cap is the
# guard the docstring already asks callers to enforce. Default 0 means "no cap":
# a self-hosted operator converting their own documents keeps the permissive
# behavior and byte-identical output, while a hosted demo sets the env var to a
# finite page budget. (#208)
DEFAULT_OCR_MAX_PAGES = 0


def get_max_pages() -> int:
    """Page budget for the OCR pre-pass; 0 (the default) disables the cap.

    A malformed or non-numeric `MD_BRIDGE_OCR_MAX_PAGES` falls back to the
    permissive default rather than failing the request.
    """
    raw = os.getenv("MD_BRIDGE_OCR_MAX_PAGES")
    if raw is None or not raw.strip():
        return DEFAULT_OCR_MAX_PAGES
    try:
        value = int(raw.strip())
    except ValueError:
        return DEFAULT_OCR_MAX_PAGES
    return value if value > 0 else DEFAULT_OCR_MAX_PAGES


# Per-page wall-clock budget for the Tesseract call. MD_BRIDGE_OCR_MAX_PAGES
# caps how many pages run, not how long one page may take, so a single dense
# page could pin the worker thread forever. The repo rule is that every
# subprocess invocation carries an explicit timeout (#364).
DEFAULT_OCR_PAGE_TIMEOUT = 60
DEFAULT_OCR_IMAGE_TIMEOUT = 5


def get_page_timeout() -> int:
    """Seconds a single page's Tesseract run may take before it is killed.

    A malformed or non-positive `MD_BRIDGE_OCR_PAGE_TIMEOUT` falls back to the
    default rather than failing the request.
    """
    raw = os.getenv("MD_BRIDGE_OCR_PAGE_TIMEOUT")
    if raw is None or not raw.strip():
        return DEFAULT_OCR_PAGE_TIMEOUT
    try:
        value = int(raw.strip())
    except ValueError:
        return DEFAULT_OCR_PAGE_TIMEOUT
    return value if value > 0 else DEFAULT_OCR_PAGE_TIMEOUT


def get_image_timeout() -> int:
    """Seconds allowed for one embedded-image OCR subprocess.

    Image OCR is additive to a successful conversion, so its smaller default
    avoids one noisy screenshot holding the whole request hostage. Operators
    can raise the budget without affecting full-page scan OCR.
    """
    raw = os.getenv("MD_BRIDGE_OCR_IMAGE_TIMEOUT")
    if raw is None or not raw.strip():
        return DEFAULT_OCR_IMAGE_TIMEOUT
    try:
        value = int(raw.strip())
    except ValueError:
        return DEFAULT_OCR_IMAGE_TIMEOUT
    return value if value > 0 else DEFAULT_OCR_IMAGE_TIMEOUT


def ocr_stack_available() -> bool:
    """True when both halves of the OCR stack are installed: the Tesseract
    binary on PATH and the `pytesseract` Python binding (the `[ocr]` extra)."""
    if shutil.which("tesseract") is None:
        return False
    try:
        import pytesseract  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError:
        return False
    return True


class ImageOcrProcessor:
    """Request-scoped image OCR callback for the lean PDF converter.

    The converter owns page geometry and ordering. This small object owns the
    optional Pillow/Tesseract work, including a bounded per-request LRU keyed
    by the original image bytes. Keeping it request-scoped prevents a server
    process from retaining user image content or OCR output between requests.
    """

    def __init__(self, *, mode: str, lang: str) -> None:
        self.mode = mode
        self.lang = lang
        self._eligible: dict[str, bool] = {}
        self._cache: OrderedDict[str, str | None] = OrderedDict()
        self.warnings: list[str] = []
        self.applied = False

    def _warn(self, code: str) -> None:
        if code not in self.warnings:
            self.warnings.append(code)

    @staticmethod
    def _open_image(image_bytes: bytes):
        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes))
        image.load()
        return image

    @staticmethod
    def _has_text_density(image) -> bool:
        """Return whether an image is unlike a flat fill or smooth photo.

        The 16-bin histogram is intentionally small and deterministic. Alpha
        is composited on white first so transparent PNG diagrams are evaluated
        by their visible pixels rather than arbitrary transparent RGB values.
        """
        from PIL import Image, ImageStat

        if image.mode == "CMYK":
            return False
        if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
            rgba = image.convert("RGBA")
            background = Image.new("RGBA", rgba.size, "white")
            image = Image.alpha_composite(background, rgba).convert("RGB")
        gray = image.convert("L")
        histogram = gray.histogram()
        bins = [sum(histogram[offset : offset + 16]) for offset in range(0, 256, 16)]
        total = sum(bins)
        if not total:
            return False
        densest_pair = max((bins[index] + bins[index + 1] for index in range(15)), default=0)
        if densest_pair / total >= 0.8:
            return False
        return ImageStat.Stat(gray).var[0] >= 100

    def is_candidate(self, image_bytes: bytes, _extension: str) -> bool:
        """Run the Pillow-only portion of the deterministic auto filter."""
        digest = sha256(image_bytes).hexdigest()
        cached = self._eligible.get(digest)
        if cached is not None:
            return cached
        try:
            image = self._open_image(image_bytes)
            eligible = image.mode != "CMYK" and (
                self.mode == "all" or self._has_text_density(image)
            )
        except Exception:
            eligible = False
        self._eligible[digest] = eligible
        return eligible

    @staticmethod
    def _lines_from_data(data: dict[str, list]) -> str:
        lines: dict[tuple[int, int, int], list[str]] = {}
        for index, raw in enumerate(data.get("text", [])):
            word = str(raw).strip()
            if not word:
                continue
            key = tuple(
                int(data.get(field, [0] * (index + 1))[index])
                for field in ("block_num", "par_num", "line_num")
            )
            lines.setdefault(key, []).append(word)
        return "\n".join(" ".join(words) for _, words in sorted(lines.items()))

    def __call__(self, image_bytes: bytes, _extension: str) -> str | None:
        """Return OCR text, or no text when this image cannot be transcribed."""
        digest = sha256(image_bytes).hexdigest()
        if digest in self._cache:
            self._cache.move_to_end(digest)
            return self._cache[digest]

        import pytesseract

        try:
            image = self._open_image(image_bytes)
            data = pytesseract.image_to_data(
                image,
                lang=self.lang,
                output_type=pytesseract.Output.DICT,
                timeout=get_image_timeout(),
            )
        except pytesseract.TesseractError:
            # A Tesseract failure (missing binary or langpack, malformed image)
            # is not a timeout. TesseractError subclasses RuntimeError, so it
            # must be caught first or the RuntimeError arm below would mislabel
            # it as ocr_image_timeout (mirrors the page path, ocr.py ocr_pdf_bytes).
            self._warn("ocr_image_failed")
            text = None
        except RuntimeError:
            # pytesseract raises a plain RuntimeError when it kills a run that
            # overran the per-image timeout.
            self._warn("ocr_image_timeout")
            text = None
        except Exception:
            self._warn("ocr_image_failed")
            text = None
        else:
            text = self._lines_from_data(data).strip() or None
            confidences: list[float] = []
            for value in data.get("conf", []):
                try:
                    confidence = float(value)
                except (TypeError, ValueError):
                    continue
                if confidence >= 0:
                    confidences.append(confidence)
            if confidences and sum(confidences) / len(confidences) < 60:
                self._warn("ocr_image_low_confidence")
            if text:
                self.applied = True

        self._cache[digest] = text
        if len(self._cache) > 256:
            self._cache.popitem(last=False)
        return text


def is_enabled() -> bool:
    """Whether the OCR pre-pass should run for a scanned PDF.

    The default is automatic: OCR runs when the stack is actually installed,
    because installing the `[ocr]` extra or the `runtime-ocr` image *is* the
    act of opting in. A lean base install carries neither the binary nor the
    binding, so OCR stays off and a scanned PDF returns the same 422
    `ocr_required` as before. `MD_BRIDGE_OCR_ENABLED` overrides the auto
    decision either way: `1`/`true`/`yes`/`on` forces it on, `0`/`false`/`no`/
    `off` forces it off (e.g. to keep a slow OCR pass out of a hot path).
    """
    flag = os.getenv("MD_BRIDGE_OCR_ENABLED")
    if flag is not None and flag.strip():
        value = flag.strip().lower()
        if value in _TRUTHY:
            return True
        if value in _FALSY:
            return False
    return ocr_stack_available()


def image_ocr_enabled() -> bool:
    """Whether per-image OCR (#140) may run for a request that asked for it.

    Unlike the page pre-pass (`is_enabled`, which opts in automatically when the
    stack is installed), image OCR requires the operator to opt in EXPLICITLY via
    a truthy `MD_BRIDGE_OCR_ENABLED`, AND the stack to be present. A truthy flag
    with the binary missing still returns False, so the caller raises the same
    422 `ocr_not_available` instead of failing mid-conversion. This keeps a slow,
    per-image Tesseract pass off a hot path unless it was deliberately enabled.
    """
    flag = os.getenv("MD_BRIDGE_OCR_ENABLED", "").strip().lower()
    return flag in _TRUTHY and ocr_stack_available()


def ocr_pdf_bytes(pdf_bytes: bytes, lang: str = DEFAULT_OCR_LANG) -> bytes:
    """Return a new PDF with a searchable text layer over each rasterized page.

    This rasterizes every page at 300 DPI and can be memory/time heavy; callers
    should enforce upload or page-count limits before enabling OCR in production.
    """

    import pytesseract
    from PIL import Image

    timeout = get_page_timeout()
    src = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    out = pymupdf.open()
    try:
        for page_index, page in enumerate(src):
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))

            try:
                pdf_page_bytes = pytesseract.image_to_pdf_or_hocr(
                    img, lang=lang, extension="pdf", timeout=timeout
                )
            except pytesseract.TesseractError:
                # A non-zero Tesseract exit (e.g. partially installed language
                # data) is not a timeout. TesseractError subclasses RuntimeError,
                # so re-raise it here and let the caller's language-data guidance
                # handle it instead of mislabeling it as a timeout (#364).
                raise
            except RuntimeError as exc:
                # pytesseract raises a plain RuntimeError when it kills a run that
                # exceeded the timeout. Name the page so the operator can raise
                # the budget or split the document (#364).
                raise ApiError(
                    500,
                    "ocr_failed",
                    f"OCR timed out on page {page_index + 1} after {timeout}s. "
                    "Raise MD_BRIDGE_OCR_PAGE_TIMEOUT or split the document.",
                    detail=str(exc),
                ) from exc
            page_pdf = pymupdf.open(stream=pdf_page_bytes, filetype="pdf")
            try:
                out.insert_pdf(page_pdf)
            finally:
                page_pdf.close()

        return out.tobytes()

    finally:
        out.close()
        src.close()
