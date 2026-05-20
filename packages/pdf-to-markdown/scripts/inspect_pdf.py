"""Inspect a PDF's font usage to inform heuristics.

Usage: python inspect_pdf.py <pdf_path> [--max-pages N]

Prints a histogram of (font_size, font_name, flags) -> count, sample lines,
and a guess for body size + heading levels.
"""
from __future__ import annotations

import argparse
import io
import sys
from collections import Counter
from pathlib import Path

import fitz  # PyMuPDF
from pypdf import PdfReader

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def check_tagged(pdf_path: Path) -> dict:
    """Detect tagged-PDF structure (PDF/UA, accessibility tags).

    Returns a small report describing what's available.
    """
    info = {"tagged": False, "marked": False, "struct_tree": False, "top_tags": []}
    try:
        reader = PdfReader(str(pdf_path))
        catalog = reader.trailer.get("/Root", {})
        try:
            catalog = catalog.get_object() if hasattr(catalog, "get_object") else catalog
        except Exception:
            # pypdf raises on malformed indirect references; fall back to the
            # raw value so the rest of the inspection still runs.
            pass

        mark_info = catalog.get("/MarkInfo")
        if mark_info is not None:
            try:
                mark_info = mark_info.get_object()
            except Exception:
                # See note above: keep the raw object on resolution failure.
                pass
            info["marked"] = bool(mark_info.get("/Marked", False))

        struct_root = catalog.get("/StructTreeRoot")
        if struct_root is not None:
            info["struct_tree"] = True
            try:
                struct_root = struct_root.get_object()
            except Exception:
                # See note above: keep the raw object on resolution failure.
                pass

            tag_counter: Counter[str] = Counter()
            def walk(node, depth=0):
                if depth > 5:
                    return
                try:
                    node = node.get_object() if hasattr(node, "get_object") else node
                except Exception:
                    # A node we cannot resolve is a node we cannot count.
                    return
                if isinstance(node, dict):
                    tag = node.get("/S")
                    if tag:
                        tag_counter[str(tag)] += 1
                    kids = node.get("/K")
                    if kids is not None:
                        try:
                            kids = kids.get_object()
                        except Exception:
                            # See note above: keep the raw value and let the
                            # isinstance branches below sort it out.
                            pass
                        if isinstance(kids, list):
                            for k in kids:
                                walk(k, depth + 1)
                        else:
                            walk(kids, depth + 1)
            walk(struct_root)
            info["top_tags"] = tag_counter.most_common(15)
        info["tagged"] = info["marked"] and info["struct_tree"]
    except Exception as e:
        info["error"] = str(e)
    return info


def flag_str(flags: int) -> str:
    parts = []
    if flags & 2 ** 0:
        parts.append("superscript")
    if flags & 2 ** 1:
        parts.append("italic")
    if flags & 2 ** 4:
        parts.append("bold")
    if flags & 2 ** 2:
        parts.append("serif")
    if flags & 2 ** 3:
        parts.append("mono")
    return ",".join(parts) or "-"


def inspect(pdf_path: Path, max_pages: int | None) -> None:
    doc = fitz.open(pdf_path)
    n_pages = len(doc) if max_pages is None else min(len(doc), max_pages)

    size_counter: Counter[float] = Counter()
    font_counter: Counter[tuple[float, str, int]] = Counter()
    samples: dict[tuple[float, str, int], str] = {}

    for page_idx in range(n_pages):
        page = doc[page_idx]
        data = page.get_text("dict")
        for block in data.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    size = round(span["size"], 1)
                    font = span["font"]
                    flags = span["flags"]
                    text = span["text"].strip()
                    if not text:
                        continue
                    char_count = len(text)
                    size_counter[size] += char_count
                    key = (size, font, flags)
                    font_counter[key] += char_count
                    if key not in samples:
                        samples[key] = text[:80]

    print(f"Pages inspected: {n_pages}")
    print()
    print("Top font sizes by char count:")
    for size, count in size_counter.most_common(15):
        print(f"  {size:>6}pt  {count:>8} chars")
    print()
    print("Top (size, font, flags) by char count:")
    for (size, font, flags), count in font_counter.most_common(25):
        sample = samples[(size, font, flags)]
        print(
            f"  {size:>6}pt  {font:<40}  [{flag_str(flags):<20}]  "
            f"{count:>6}  | {sample}"
        )

    body_size = size_counter.most_common(1)[0][0]
    print()
    print(f"Inferred body size: {body_size}pt")
    bigger = sorted({s for s in size_counter if s > body_size}, reverse=True)
    print(f"Larger sizes (heading candidates, desc): {bigger}")

    print()
    print("=" * 60)
    tag_info = check_tagged(pdf_path)
    if "error" in tag_info:
        print(f"Tagged-PDF check error: {tag_info['error']}")
    else:
        print(f"Tagged PDF: {tag_info['tagged']}")
        print(f"  /MarkInfo /Marked: {tag_info['marked']}")
        print(f"  /StructTreeRoot present: {tag_info['struct_tree']}")
        if tag_info["top_tags"]:
            print("  Top structure tags:")
            for tag, count in tag_info["top_tags"]:
                print(f"    {tag:<20} {count}")
        else:
            print("  (no tags found at shallow depth)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", type=Path)
    parser.add_argument("--max-pages", type=int, default=None)
    args = parser.parse_args()

    if not args.pdf_path.exists():
        print(f"File not found: {args.pdf_path}", file=sys.stderr)
        return 1
    inspect(args.pdf_path, args.max_pages)
    return 0


if __name__ == "__main__":
    sys.exit(main())
