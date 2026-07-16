import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { fetchThemeCss } from '../lib/api'

// A live, theme-styled Markdown preview (#392, #397). Renders `markdown` with
// default.css + the theme's overlay (+ optional extraCss) inside an isolated
// iframe, so the theme's document styles never leak into the app. The content
// mounts through a React portal into the iframe, not react-dom/server, so it
// adds no bundle weight. Offline: the CSS comes from the same-origin API.

const FRAME_DOC =
  '<!doctype html><html><head><meta charset="utf-8"></head>' +
  '<body><div id="root"></div></body></html>'

interface ThemedPreviewProps {
  /** Theme slug whose overlay stacks on default.css. `default` uses the base alone. */
  themeSlug: string
  /** Markdown to render inside the themed frame. */
  markdown: string
  /** iframe title (accessible name). */
  title: string
  /** Optional user CSS applied after the theme, like the converter stacks it. */
  extraCss?: string
  className?: string
}

export function ThemedPreview({
  themeSlug,
  markdown,
  title,
  extraCss = '',
  className,
}: ThemedPreviewProps) {
  const [root, setRoot] = useState<HTMLElement | null>(null)
  const [baseCss, setBaseCss] = useState('')
  // The overlay is tagged with the slug it belongs to, so a stale overlay from
  // the previously selected theme is never applied while a new one loads.
  const [overlay, setOverlay] = useState<{ slug: string; css: string }>({ slug: '', css: '' })

  // default.css is the base every theme stacks on; fetch it once.
  useEffect(() => {
    const ac = new AbortController()
    fetchThemeCss('default', ac.signal)
      .then(setBaseCss)
      .catch(() => setBaseCss(''))
    return () => ac.abort()
  }, [])

  // Fetch the theme's overlay. `default` needs none (the base alone), so skip it.
  useEffect(() => {
    if (!themeSlug || themeSlug === 'default') return
    const ac = new AbortController()
    fetchThemeCss(themeSlug, ac.signal)
      .then((css) => setOverlay({ slug: themeSlug, css }))
      .catch(() => setOverlay({ slug: themeSlug, css: '' }))
    return () => ac.abort()
  }, [themeSlug])

  // Apply the overlay only once it matches the current theme; while a switch is
  // in flight the loaded overlay is for the old theme, so fall back to the base.
  const overlayCss =
    themeSlug !== 'default' && overlay.slug === themeSlug ? overlay.css : ''
  const css = `${baseCss}\n${overlayCss}\n${extraCss}`

  return (
    <>
      <iframe
        className={className}
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
