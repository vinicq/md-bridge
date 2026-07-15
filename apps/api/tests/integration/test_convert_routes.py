"""Route-level regressions for the conversion endpoints.

These exercise the HTTP surface (headers, error envelope) rather than the
conversion output, so they stay fast and need no Chromium.
"""
from __future__ import annotations

from email.message import Message

from app.main import create_app
from fastapi.testclient import TestClient


def _client() -> TestClient:
    return TestClient(create_app())


def _raw_multipart(filename: str, payload: bytes = b"# hi\n") -> tuple[bytes, dict[str, str]]:
    """Hand-build a multipart body so the part filename reaches the server
    verbatim. httpx percent-escapes quotes/CRLF in filenames; a naive client
    (curl, a hand-rolled uploader) does not, which is the #362 attack path."""
    boundary = "boundarytest362"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        "Content-Type: text/markdown\r\n\r\n"
    ).encode() + payload + f"\r\n--{boundary}--\r\n".encode()
    return body, {"Content-Type": f"multipart/form-data; boundary={boundary}"}


def _parsed_filename(header: str) -> str | None:
    msg = Message()
    msg["Content-Disposition"] = header
    return msg.get_filename()


def test_content_disposition_survives_quote_in_filename():
    # A filename with an embedded quote must not corrupt the header (#362).
    # Before the fix the raw quote closed the value early:
    # `attachment; filename="evil"name.docx"`.
    client = _client()
    body, headers = _raw_multipart('evil"name.md')
    resp = client.post("/api/md-to-docx", content=body, headers=headers)
    assert resp.status_code == 200, resp.text

    cd = resp.headers["content-disposition"]
    # No CR/LF may leak into the header value.
    assert "\r" not in cd and "\n" not in cd, repr(cd)
    # A standard parser must recover the sanitized name intact, not a truncated
    # `evil` cut off at the injected quote.
    assert _parsed_filename(cd) == "evilname.docx", cd


def test_content_disposition_ascii_fallback_for_non_ascii_name():
    # An all-non-ASCII stem must still yield a usable ASCII fallback name, not
    # an extension-only hidden file, for clients that ignore filename* (#362).
    client = _client()
    body, headers = _raw_multipart("レポート.md")
    resp = client.post("/api/md-to-docx", content=body, headers=headers)
    assert resp.status_code == 200, resp.text
    cd = resp.headers["content-disposition"]
    assert 'filename="document.docx"' in cd, cd
    # The real name survives in filename* (percent-encoded UTF-8).
    assert "filename*=UTF-8''" in cd, cd


def test_content_disposition_strips_path_separators():
    client = _client()
    body, headers = _raw_multipart("../../etc/passwd.md")
    resp = client.post("/api/md-to-docx", content=body, headers=headers)
    assert resp.status_code == 200, resp.text
    name = _parsed_filename(resp.headers["content-disposition"])
    assert name and "/" not in name and "\\" not in name, resp.headers["content-disposition"]
