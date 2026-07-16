# Theme reference renders

A representative subset of the registered Markdown → PDF themes, each rendered
from a single shared sample so the visual identities can be compared side by
side. Not every theme has a render committed; the set covers the families
(serif / sans-serif / monospace) rather than duplicating one PDF per theme.

| File | Theme | Identity |
| --- | --- | --- |
| `default.pdf` | `default` | Neutral A4 base, sans-serif, boxed table header. |
| `academic.pdf` | `academic` | Serif, justified body, centered h1, decimal section numbering. |
| `business.pdf` | `business` | Sans-serif, red accent masthead, accent table header. |
| `minimal.pdf` | `minimal` | Low-chrome draft layout, left-aligned, rule-only tables. |
| `novel.pdf` | `novel` | Serif book layout: Garamond, centered chapter titles, indented justified prose, drop cap. |
| `whitepaper.pdf` | `whitepaper` | Sans-serif whitepaper: teal accent, masthead title band, generous leading, striped tables. |
| `notebook.pdf` | `notebook` | Monospace lab-notebook: mono body, blue accents, left-bar sections, tinted tables. |

The themes are CSS overlays stacked on `default.css`
(`packages/markdown-to-pdf/templates/`). The source sample is the markdown in
`tests/regression/test_md_to_pdf_regression.py`.

## Renderer limitations

The converter prints through headless Chromium with fixed page margins and no
running header/footer support, so the theme stylesheets cannot express
per-theme page margins or a repeating footer page number yet. These need a
converter change and are tracked as a follow-up. The CSS files document the
constraint inline.

## Regenerating

Re-render after any change to a theme stylesheet. Each PDF is the shared sample
rendered with `[default.css]` for `default` and `[default.css, <slug>.css]` for
the others, matching the registry's stacking contract.
