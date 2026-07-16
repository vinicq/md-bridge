import { useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useThemes } from '../hooks/useThemes'
import { fetchThemeCss } from '../lib/api'
import { Button } from '../components/Button'
import { useTranslation } from '../i18n'
import { PREVIEW_SAMPLES, type PreviewSampleId } from '../lib/previewSamples'
import './Themes.css'

// The redesign theme library (F2, #392). Mirrors designer/md-bridge.dc.html:
// a grid of every API theme, a family filter, a live preview that stacks the
// theme (and optional custom CSS) over default.css in an isolated iframe, and
// read-only theme CSS. Themes come from GET /api/themes; nothing is hardcoded.

// The ten overlays the redesign pack added (#393). Used only to badge them NEW.
const NEW_THEMES = new Set([
  'letter',
  'manuscript',
  'newsprint',
  'notebook',
  'novel',
  'resume',
  'slate',
  'slides',
  'techbook',
  'whitepaper',
])

type Family = 'serif' | 'sans' | 'mono' | 'other'
type FilterValue = 'all' | 'serif' | 'sans' | 'mono'

// The API family values are inconsistent (serif / sans / sans-serif / monospace
// / general). Fold them into the three buckets the filter offers; anything else
// (e.g. `general`) only shows under "All".
function normalizeFamily(family: string): Family {
  const f = family.toLowerCase()
  if (f === 'serif') return 'serif'
  if (f === 'sans' || f === 'sans-serif') return 'sans'
  if (f === 'mono' || f === 'monospace') return 'mono'
  return 'other'
}

type SampleMode = PreviewSampleId | 'diagram'

// The Diagram mode shows the Mermaid source as a code block (the browser preview
// does not run Mermaid; the diagram renders in the actual PDF, #394).
const DIAGRAM_SAMPLE = [
  '# Diagram',
  '',
  '```mermaid',
  'flowchart LR',
  '  A[PDF] --> B[Markdown]',
  '  B --> C{Theme}',
  '  C --> D[Styled PDF]',
  '```',
].join('\n')

const SAMPLE_MARKDOWN = {
  ...Object.fromEntries(PREVIEW_SAMPLES.map((s) => [s.id, s.markdown])),
  diagram: DIAGRAM_SAMPLE,
} as Record<SampleMode, string>

const SAMPLE_ORDER: SampleMode[] = [
  'document',
  'article',
  'resume',
  'email',
  'contract',
  'blog',
  'diagram',
]

// A blank document with a mount point. The preview renders the theme <style>
// and the sample into #root with a React portal, so the theme CSS is fully
// isolated from the app and nothing is fetched over the network.
const FRAME_DOC =
  '<!doctype html><html><head><meta charset="utf-8"></head>' +
  '<body><div id="root"></div></body></html>'

function download(name: string, text: string, type: string): void {
  const url = URL.createObjectURL(new Blob([text], { type }))
  const a = document.createElement('a')
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

interface PreviewFrameProps {
  css: string
  markdown: string
  title: string
}

// Renders the sample into an isolated iframe via a portal (no react-dom/server,
// so no bundle cost). The theme CSS is a declarative <style> in the portal, so
// React keeps it in sync when the theme or custom CSS changes.
function PreviewFrame({ css, markdown, title }: PreviewFrameProps) {
  const [root, setRoot] = useState<HTMLElement | null>(null)

  return (
    <>
      <iframe
        className="theme-lib__frame"
        title={title}
        srcDoc={FRAME_DOC}
        onLoad={(e) => {
          const node = e.currentTarget.contentDocument?.getElementById('root')
          if (node) setRoot(node)
        }}
      />
      {root &&
        createPortal(
          <>
            <style>{css}</style>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
          </>,
          root,
        )}
    </>
  )
}

export function Themes() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { themes } = useThemes()
  const lib = t.themeLib

  const [filter, setFilter] = useState<FilterValue>('all')
  const [picked, setPicked] = useState<string>('')
  const [tab, setTab] = useState<'custom' | 'source'>('custom')
  const [customCss, setCustomCss] = useState('')
  const [sampleMode, setSampleMode] = useState<SampleMode>('document')

  const [baseCss, setBaseCss] = useState('')
  const [sourceCss, setSourceCss] = useState('')

  // Derive the active theme rather than store it in an effect: the user's pick
  // if any, else Academic (a rich serif), else the first theme.
  const active =
    picked || themes.find((x) => x.slug === 'academic')?.slug || themes[0]?.slug || ''

  // default.css is the base every theme stacks on; fetch it once.
  useEffect(() => {
    const ac = new AbortController()
    fetchThemeCss('default', ac.signal)
      .then(setBaseCss)
      .catch(() => setBaseCss(''))
    return () => ac.abort()
  }, [])

  // The active theme's own overlay drives the Source tab, the download, and
  // (for non-default) the preview stack.
  useEffect(() => {
    if (!active) return
    const ac = new AbortController()
    fetchThemeCss(active, ac.signal)
      .then(setSourceCss)
      .catch(() => setSourceCss(''))
    return () => ac.abort()
  }, [active])

  const visible = useMemo(
    () => themes.filter((theme) => filter === 'all' || normalizeFamily(theme.family) === filter),
    [themes, filter],
  )

  const stackedCss =
    (active === 'default' ? baseCss : `${baseCss}\n${sourceCss}`) + `\n${customCss}`

  const activeTheme = themes.find((x) => x.slug === active)
  const familyLabel: Record<FilterValue, string> = {
    all: lib.all,
    serif: lib.serif,
    sans: lib.sans,
    mono: lib.mono,
  }

  function sampleLabel(mode: SampleMode): string {
    return mode === 'diagram' ? lib.diagram : t.previewSamples[mode]
  }

  return (
    <div className="page container theme-lib">
      <header className="page__head">
        <h1>{lib.title}</h1>
        <p>{lib.subtitle}</p>
      </header>

      <div className="theme-lib__filter" role="group" aria-label={lib.filter}>
        {(['all', 'serif', 'sans', 'mono'] as FilterValue[]).map((value) => (
          <button
            key={value}
            type="button"
            className="theme-lib__chip"
            aria-pressed={filter === value}
            onClick={() => setFilter(value)}
          >
            {familyLabel[value]}
          </button>
        ))}
      </div>

      <div className="theme-lib__layout">
        <ul className="theme-lib__grid" aria-label={lib.title}>
          {visible.map((theme) => (
            <li key={theme.slug}>
              <button
                type="button"
                className="theme-lib__tile"
                aria-pressed={active === theme.slug}
                onClick={() => {
                  // Drop the previous theme's CSS immediately so the preview,
                  // the source tab, and the download never show stale content
                  // under the newly selected theme while its CSS loads.
                  setSourceCss('')
                  setPicked(theme.slug)
                }}
              >
                <span className="theme-lib__tile-name">{theme.name}</span>
                <span className="theme-lib__tile-family">{normalizeFamily(theme.family)}</span>
                {NEW_THEMES.has(theme.slug) && <span className="theme-lib__new">{lib.newBadge}</span>}
              </button>
            </li>
          ))}
        </ul>

        <section className="theme-lib__preview" aria-label={lib.preview}>
          <div className="theme-lib__samples" role="group" aria-label={lib.preview}>
            {SAMPLE_ORDER.map((mode) => (
              <button
                key={mode}
                type="button"
                className="theme-lib__sample-tab"
                aria-pressed={sampleMode === mode}
                onClick={() => setSampleMode(mode)}
              >
                {sampleLabel(mode)}
              </button>
            ))}
          </div>

          <PreviewFrame css={stackedCss} markdown={SAMPLE_MARKDOWN[sampleMode]} title={lib.preview} />

          <div className="theme-lib__actions">
            <Button
              variant="primary"
              disabled={!active}
              onClick={() => navigate(`/convert/md-to-pdf?theme=${encodeURIComponent(active)}`)}
            >
              {lib.use}
            </Button>
            <Button
              variant="ghost"
              disabled={!sourceCss}
              onClick={() => download(`${active}.css`, sourceCss, 'text/css')}
            >
              {lib.downloadCss}
            </Button>
          </div>

          <div className="theme-lib__tabs" role="tablist" aria-label={activeTheme?.name ?? ''}>
            <button
              type="button"
              role="tab"
              aria-selected={tab === 'custom'}
              className="theme-lib__tab"
              onClick={() => setTab('custom')}
            >
              {lib.custom}
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={tab === 'source'}
              className="theme-lib__tab"
              onClick={() => setTab('source')}
            >
              {lib.source} <span className="theme-lib__readonly">({lib.readonly})</span>
            </button>
          </div>

          {tab === 'custom' ? (
            <div className="theme-lib__panel">
              <p className="theme-lib__hint">{lib.customHint}</p>
              <textarea
                className="theme-lib__css"
                aria-label={lib.custom}
                value={customCss}
                spellCheck={false}
                onChange={(e) => setCustomCss(e.target.value)}
              />
              <Button variant="ghost" disabled={!customCss} onClick={() => setCustomCss('')}>
                {lib.clear}
              </Button>
            </div>
          ) : (
            <div className="theme-lib__panel">
              <pre className="theme-lib__css theme-lib__css--source" aria-label={lib.source}>
                {sourceCss}
              </pre>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
