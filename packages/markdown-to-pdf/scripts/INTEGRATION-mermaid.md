# Integrating Mermaid into convert.py

mermaid_render.py is self-contained; wiring it into the pipeline is four small
edits to scripts/convert.py. Every edit is a no-op for documents without a
mermaid block, so existing renders and regression goldens stay byte-for-byte
identical.

## 1. Import the module (after the Playwright import)

~~~python
from playwright.sync_api import sync_playwright

import mermaid_render   # <-- add
~~~

## 2. Let build_html accept injected HTML

~~~python
def build_html(
    body_html: str, fm: dict, lang: str, css_blocks: list[str], base_uri: str = "",
    extra_head: str = "", body_tail: str = "",          # <-- add
) -> str:
~~~

Just before the "return (" inside build_html, add:

~~~python
    head_extra = ("\n" + extra_head) if extra_head else ""
    body_extra = ("\n" + body_tail) if body_tail else ""
~~~

Then change the two f-string lines so the injected blocks land in place (when
both are empty the output is unchanged):

~~~python
        f'{style}{head_extra}\n'      # was: f'{style}\n'
        '</head>\n'
        '<body>\n'
        f'{body_html}{body_extra}\n'  # was: f'{body_html}\n'
~~~

## 3. Wait for async rendering in render_to_pdf

~~~python
def render_to_pdf(html: str, pdf_path: Path, base_url: Path,
                  pdf_kwargs: dict | None = None,
                  ready_flag: str | None = None) -> None:   # <-- add param
    ...
            page.set_content(html, wait_until="load", timeout=30000)
            if ready_flag:
                # Mermaid renders asynchronously; wait for the init script flag
                # so no diagram is captured half-drawn.
                page.wait_for_function(f"window['{ready_flag}'] === true", timeout=20000)
            page.pdf(path=str(pdf_path), **kwargs)
~~~

## 4. Drive it from convert()

Right after body_html = markdown.markdown(...):

~~~python
    # Mermaid: rewrite mermaid fences and inject the vendored bundle so Chromium
    # renders diagrams to SVG before printing.
    body_html, _mmd_count = mermaid_render.transform_blocks(body_html)
    extra_head = body_tail = ""
    ready_flag = None
    if _mmd_count:
        extra_head, body_tail = mermaid_render.assets()
        ready_flag = mermaid_render.READY_FLAG
        if not mermaid_render.MERMAID_JS.exists():
            print("[warn] mermaid blocks found but vendor/mermaid.min.js is missing; "
                  "diagram source will render as plain text", file=sys.stderr)
~~~

Then pass the new values into the two calls at the end of convert():

~~~python
    html = build_html(body_html, fm, lang, css_blocks, base_uri=base_uri,
                      extra_head=extra_head, body_tail=body_tail)
    ...
    render_to_pdf(html, pdf_path, base_url=base_dir,
                  pdf_kwargs=pdf_kwargs, ready_flag=ready_flag)
~~~

That is all. mermaid_render handles detection, the container CSS, the inlined
bundle, and the deterministic init.
