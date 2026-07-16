# vendor/

Third-party bundles committed for offline, deterministic rendering. The render
sandbox blocks all network egress, so anything the renderer needs must live here
and be inlined -- never fetched.

## mermaid.min.js

Mermaid support (scripts/mermaid_render.py) inlines this file as a classic
<script>, so it must be a UMD build that exposes a global "mermaid".

Fetch a pinned UMD build once and commit it:

~~~bash
curl -L -o packages/markdown-to-pdf/vendor/mermaid.min.js \
  https://cdn.jsdelivr.net/npm/mermaid@10.9.3/dist/mermaid.min.js
~~~

Notes:

- Pin the version. 10.9.3 ships a UMD mermaid.min.js with a global "mermaid",
  which the inline init relies on. If you bump, re-check that dist/mermaid.min.js
  is still UMD (some newer lines ship ESM-only .mjs, which cannot be inlined as a
  classic script).
- Size is ~2-3 MB minified. It is committed on purpose: the converter must render
  without network access.
- License: Mermaid is MIT. Keep its license/notice alongside if your policy
  requires it.
- The file is optional. Without it the pipeline still runs: mermaid blocks fall
  back to plain monospace text and a warning is printed.
