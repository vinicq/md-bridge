"""Theme registry for Markdown -> PDF rendering (#23).

A theme is a CSS stylesheet under `packages/markdown-to-pdf/templates/` plus
optional metadata in a sibling `<slug>.theme.json`. The renderer stacks the
selected theme on top of `default.css`, so every non-default theme is an overlay
that only carries its overrides; `default` renders the base alone.

The registry scans the templates directory once at import and caches the result
in process. There is no persistence and no hot-reload: a template added or
edited on disk needs a service restart, which is the deployment model for a
self-hosted, deterministic converter.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.config import MD_TO_PDF_TEMPLATES
from app.errors import ApiError

log = logging.getLogger(__name__)

DEFAULT_SLUG = "default"


class UnknownThemeError(ApiError):
    """Raised when a request asks for a theme slug that is not registered."""

    def __init__(self, slug: str) -> None:
        super().__init__(
            400,
            "unknown_theme",
            f"Theme '{slug}' is not registered.",
        )
        self.slug = slug


@dataclass(frozen=True)
class Theme:
    slug: str
    name: str
    description: str
    family: str
    version: str
    css_path: Path  # the theme's own stylesheet (the overlay; default's base)

    def to_dict(self) -> dict[str, str]:
        return {
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "family": self.family,
        }


def _load_metadata(slug: str, meta_path: Path) -> dict[str, str]:
    """Read `<slug>.theme.json`, tolerating a missing file or missing fields.

    A missing `name` falls back to the capitalised slug; everything else falls
    back to an empty string or a 0.0.0 version, so a bare `<slug>.css` with no
    metadata still registers.
    """
    data: dict[str, object] = {}
    if meta_path.exists():
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("theme metadata unreadable for %s: %s; using defaults", slug, exc)
            data = {}
    return {
        "name": str(data.get("name") or slug.capitalize()),
        "description": str(data.get("description") or ""),
        "family": str(data.get("family") or "general"),
        "version": str(data.get("version") or "0.0.0"),
    }


def _scan(templates_dir: Path) -> dict[str, Theme]:
    themes: dict[str, Theme] = {}
    for css_path in sorted(templates_dir.glob("*.css")):
        slug = css_path.stem
        meta = _load_metadata(slug, templates_dir / f"{slug}.theme.json")
        themes[slug] = Theme(
            slug=slug,
            name=meta["name"],
            description=meta["description"],
            family=meta["family"],
            version=meta["version"],
            css_path=css_path,
        )
    if DEFAULT_SLUG not in themes:
        # The default base stylesheet is the one invariant of the renderer; a
        # registry without it is a deployment error, not a request error.
        raise ApiError(
            500,
            "missing_template",
            f"default theme stylesheet not found in {templates_dir}",
        )
    return themes


@lru_cache(maxsize=1)
def _registry() -> dict[str, Theme]:
    return _scan(MD_TO_PDF_TEMPLATES)


def list_themes() -> list[Theme]:
    """All registered themes, default first then the rest alphabetically."""
    themes = _registry()
    rest = sorted((t for s, t in themes.items() if s != DEFAULT_SLUG), key=lambda t: t.slug)
    return [themes[DEFAULT_SLUG], *rest]


def get_theme(slug: str) -> Theme:
    """Return the theme for `slug` or raise UnknownThemeError."""
    try:
        return _registry()[slug]
    except KeyError as exc:
        raise UnknownThemeError(slug) from exc


def css_paths_for(slug: str) -> list[Path]:
    """The stylesheets the renderer should stack for `slug`.

    `default` renders its base stylesheet alone; every other theme stacks its
    overlay on top of the default base, so a placeholder overlay still inherits
    a complete, legible layout.
    """
    theme = get_theme(slug)
    if slug == DEFAULT_SLUG:
        return [theme.css_path]
    return [_registry()[DEFAULT_SLUG].css_path, theme.css_path]
