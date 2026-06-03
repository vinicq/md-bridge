import { useEffect, useState } from 'react'
import { useTranslation } from '../i18n'
import { MarkdownPreview } from './MarkdownPreview'
import './ComparePanes.css'

export interface ComparePanesProps {
  /** Blob URL of the source PDF, or null when nothing is selected. */
  pdfUrl: string | null
  /** File name of the selected PDF, used for the iframe's accessible name. */
  pdfName: string | null
  /** Converted Markdown for the right pane. */
  markdown: string
  /** The selected item failed with a missing text layer (ocr_required). */
  sourceError?: boolean
}

type Tab = 'pdf' | 'md'

// Side-by-side source-PDF and Markdown panes (#15). Above 768px both panes are
// visible (the parent grid lays them out); at/below 768px they collapse to a
// tablist so each gets the full width. Both panes stay mounted and the inactive
// one is hidden with the `hidden` attribute, which keeps the iframe blob alive
// (no reload/flash) and removes the pane from the a11y tree and tab order.
export function ComparePanes({ pdfUrl, pdfName, markdown, sourceError = false }: ComparePanesProps) {
  const { t } = useTranslation()
  // Default to Markdown: the converted result is what the user came for, and the
  // ocr_required alert lives on that side.
  const [tab, setTab] = useState<Tab>('md')
  // Track whether we are in the tabbed (narrow) layout. Both panes render either
  // way; this only drives the tablist chrome and the `hidden` toggling.
  const [tabbed, setTabbed] = useState(false)

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return
    const mq = window.matchMedia('(max-width: 768px)')
    const sync = () => setTabbed(mq.matches)
    sync()
    mq.addEventListener('change', sync)
    return () => mq.removeEventListener('change', sync)
  }, [])

  const pdfPane = (
    <section
      className="compare__pane compare__pane--pdf"
      id="compare-panel-pdf"
      role={tabbed ? 'tabpanel' : undefined}
      aria-labelledby={tabbed ? 'compare-tab-pdf' : undefined}
      tabIndex={tabbed ? 0 : undefined}
      hidden={tabbed && tab !== 'pdf'}
    >
      {sourceError ? (
        <div className="compare__placeholder">{t.pdfToMd.sourcePaneError}</div>
      ) : pdfUrl && pdfName ? (
        <iframe
          className="compare__frame"
          src={pdfUrl}
          title={t.pdfToMd.sourceIframeTitle(pdfName)}
        />
      ) : (
        <div className="compare__placeholder">{t.pdfToMd.sourcePaneEmpty}</div>
      )}
    </section>
  )

  const mdPane = (
    <section
      className="compare__pane compare__pane--md"
      id="compare-panel-md"
      role={tabbed ? 'tabpanel' : undefined}
      aria-labelledby={tabbed ? 'compare-tab-md' : undefined}
      tabIndex={tabbed ? 0 : undefined}
      hidden={tabbed && tab !== 'md'}
    >
      <MarkdownPreview markdown={markdown} empty={t.pdfToMd.previewEmpty} />
    </section>
  )

  return (
    <div className="compare">
      {tabbed && (
        <div className="compare__tabs" role="tablist" aria-label={t.pdfToMd.compare.tablistLabel}>
          <button
            type="button"
            role="tab"
            id="compare-tab-pdf"
            aria-controls="compare-panel-pdf"
            aria-selected={tab === 'pdf'}
            className={`compare__tab ${tab === 'pdf' ? 'is-active' : ''}`.trim()}
            onClick={() => setTab('pdf')}
          >
            {t.pdfToMd.compare.tabPdf}
          </button>
          <button
            type="button"
            role="tab"
            id="compare-tab-md"
            aria-controls="compare-panel-md"
            aria-selected={tab === 'md'}
            className={`compare__tab ${tab === 'md' ? 'is-active' : ''}`.trim()}
            onClick={() => setTab('md')}
          >
            {t.pdfToMd.compare.tabMd}
          </button>
        </div>
      )}
      <div className="compare__panes">
        {pdfPane}
        {mdPane}
      </div>
    </div>
  )
}
