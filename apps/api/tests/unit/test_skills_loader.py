"""Pure-function tests for the skills loader regex and caching behavior."""
from __future__ import annotations

from app.services.skills_loader import (
    _STDIO_REBIND_RE,
    md_to_pdf_module,
    pdf_inspect_module,
    pdf_to_md_module,
)


def test_regex_matches_canonical_stdout_rebind():
    src = 'sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")'
    assert _STDIO_REBIND_RE.search(src) is not None


def test_regex_matches_stderr_rebind():
    src = 'sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")'
    assert _STDIO_REBIND_RE.search(src) is not None


def test_regex_does_not_match_unrelated_assignments():
    assert _STDIO_REBIND_RE.search("sys.path.insert(0, '/x')") is None
    assert _STDIO_REBIND_RE.search("sys.stdout.write('hi')") is None


def test_regex_does_not_eat_preceding_newline():
    """The substitution should only comment out the offending line itself,
    not collapse onto the previous line — this is the bug we fixed earlier.
    """
    src = "from pypdf import PdfReader\n\nsys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')"
    patched = _STDIO_REBIND_RE.sub(lambda m: "# stripped " + m.group(0), src)
    assert "from pypdf import PdfReader" in patched
    assert "# stripped sys.stdout" in patched
    # The original active line should no longer exist as a real statement.
    active_lines = [
        line for line in patched.splitlines()
        if line.startswith("sys.stdout = io.TextIOWrapper")
    ]
    assert active_lines == []


def test_loader_caches_each_module():
    """Each loader is lru-cached: repeated calls return the same module object."""
    assert pdf_to_md_module() is pdf_to_md_module()
    assert md_to_pdf_module() is md_to_pdf_module()
    assert pdf_inspect_module() is pdf_inspect_module()


def test_loaded_modules_expose_expected_public_api():
    pdf_mod = pdf_to_md_module()
    md_mod = md_to_pdf_module()
    inspect_mod = pdf_inspect_module()

    assert callable(pdf_mod.convert_document)
    assert callable(pdf_mod.classify_block)
    assert callable(pdf_mod.build_profile)

    assert callable(md_mod.convert)

    assert callable(inspect_mod.check_tagged)
