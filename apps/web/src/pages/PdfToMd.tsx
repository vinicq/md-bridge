import { useEffect, useRef, useState } from 'react'
import { BatchPanel } from '../components/BatchPanel'
import { ComparePanes } from '../components/ComparePanes'
import { DropZone } from '../components/DropZone'
import { OptionsPanel, type OptionField } from '../components/OptionsPanel'
import { Toast } from '../components/Toast'
import { useBatchConvert, type BatchItem } from '../hooks/useBatchConvert'
import { useBatchZip } from '../hooks/useBatchZip'
import { useInspect } from '../hooks/useInspect'
import { useTranslation } from '../i18n'
import { convertPdfToMd, type PdfToMdOptions, type PdfToMdResponse } from '../lib/api'
import { DiagnosticPanel } from '../components/DiagnosticPanel'
import './PdfToMd.css'

// The API blocks a scanned PDF with 422 ocr_required (it also returns this in
// the error detail, but the hook keeps only code+message, so the CTA target is
// a stable constant here).
const OCR_DOCS_URL =
  'https://vinicq.github.io/md-bridge/getting-started/#limits-worth-knowing-about'

function downloadText(filename: string, text: string) {
  const blob = new Blob([text], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export function PdfToMd() {
  const { t } = useTranslation()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [toast, setToast] = useState<{ kind: 'ok' | 'warn'; message: string } | null>(null)
  // Extraction options forwarded to the converter. Defaults mirror the backend
  // schema (front matter on, everything else off, heading cap 3). Options apply
  // to the next conversion; the convert closure below reads the latest value.
  const [options, setOptions] = useState<PdfToMdOptions>({
    front_matter: true,
    page_break: false,
    with_images: false,
    detect_blockquotes: false,
    cluster_headings: false,
    preserve_line_breaks: false,
    footnote_pairing: false,
    max_heading_level: 3,
  })

  const batch = useBatchConvert<PdfToMdResponse>({
    convert: (file, signal) => convertPdfToMd(file, options, signal),
    // 10-minute ceiling so a backgrounded tab cannot leave an item stuck in
    // flight forever (issue #138). Removing this line restores the old
    // no-timeout behavior.
    convertTimeoutMs: 10 * 60 * 1000,
  })
  const inspect = useInspect()
  const zip = useBatchZip<PdfToMdResponse>({
    toEntry: (it) => ({
      name: it.file.name.replace(/\.pdf$/i, '.md'),
      data: new TextEncoder().encode(it.result?.md ?? ''),
    }),
  })

  // The previewed item drives both panes (#15). The user's explicit selection
  // wins when valid; otherwise fall back to the most recent finished item, then
  // to the first item, so the source PDF shows on drop even before converting.
  const lastDoneId = [...batch.items].reverse().find((it) => it.status === 'done')?.id ?? null
  const previewFallbackId = lastDoneId ?? batch.items[0]?.id ?? null
  const effectiveSelectedId =
    selectedId && batch.items.some((it) => it.id === selectedId) ? selectedId : previewFallbackId

  const selected = batch.items.find((it) => it.id === effectiveSelectedId) ?? null

  // Inspect the previewed file (not always the first), so the diagnostic strip
  // describes the PDF currently on screen (#15).
  const selectedName = selected?.file.name
  useEffect(() => {
    if (selected?.file) void inspect.run(selected.file)
    else inspect.reset()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedName])

  // Source-PDF blob URL for the preview pane, revoked on item change and on
  // unmount so a long batch session does not leak object URLs (#15). Creating
  // and revoking the URL synchronizes with an external resource (the object URL
  // table); storing it in state is how the iframe learns the new src. Keyed on
  // the file name, not the File object, so a re-render with an equal selection
  // does not churn the URL.
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  useEffect(() => {
    const file = selected?.file
    const url = file ? URL.createObjectURL(file) : null
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPdfUrl(url)
    return () => {
      if (url) URL.revokeObjectURL(url)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedName])

  // Path A (issue #139): a pure scan comes back as a 422 ocr_required error.
  // Surface it as a prominent, focusable banner with a "how to enable OCR" CTA
  // rather than a quiet per-row line the user can miss.
  const ocrRequiredItem = batch.items.find(
    (it) => it.status === 'error' && it.error?.code === 'ocr_required',
  )
  const ocrErrorRef = useRef<HTMLHeadingElement>(null)
  useEffect(() => {
    if (ocrRequiredItem) ocrErrorRef.current?.focus()
    // Re-focus only when the offending item changes, not on every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ocrRequiredItem?.id])

  // Path B: a borderline result still converts but extracted little text.
  const selectedWarnings = selected?.result?.warnings ?? []

  // The previewed item itself failed for lack of a text layer: the PDF pane
  // shows a short placeholder instead of a misleading scanned-image render. The
  // detailed, focusable alert stays on the output side (no duplicate role=alert).
  const previewSourceError =
    selected?.status === 'error' && selected?.error?.code === 'ocr_required'

  const handleFiles = (files: File[]) => batch.add(files)

  const onOption = (id: string, value: boolean | string) => {
    setOptions((prev) => ({
      ...prev,
      [id]: id === 'max_heading_level' ? Number(value) : value,
    }))
  }

  const op = t.optionsPanel
  const optionFields: OptionField[] = [
    { id: 'front_matter', kind: 'toggle', label: op.frontMatter.label, tooltip: op.frontMatter.tip },
    { id: 'page_break', kind: 'toggle', label: op.pageBreak.label, tooltip: op.pageBreak.tip },
    { id: 'with_images', kind: 'toggle', label: op.withImages.label, tooltip: op.withImages.tip },
    { id: 'detect_blockquotes', kind: 'toggle', label: op.blockquotes.label, tooltip: op.blockquotes.tip },
    { id: 'cluster_headings', kind: 'toggle', label: op.clusterHeadings.label, tooltip: op.clusterHeadings.tip },
    { id: 'preserve_line_breaks', kind: 'toggle', label: op.preserveLineBreaks.label, tooltip: op.preserveLineBreaks.tip },
    { id: 'footnote_pairing', kind: 'toggle', label: op.footnotePairing.label, tooltip: op.footnotePairing.tip },
    {
      id: 'max_heading_level',
      kind: 'select',
      label: op.maxHeadingLevel.label,
      tooltip: op.maxHeadingLevel.tip,
      // Heading depth only applies to font-size heading detection; gray it out
      // until that toggle is on so it never reads as an inert control.
      disabled: !options.cluster_headings,
      options: [1, 2, 3, 4, 5, 6].map((n) => ({ value: String(n), label: String(n) })),
    },
  ]

  const onConvertAll = async () => {
    // Options are read by the convert closure at run time, so the queued files
    // convert with whatever is set when the user clicks. To re-convert with a
    // changed option, clear and re-add (the batch's existing idiom); the
    // "Convert all" button is correctly disabled once nothing is queued.
    await batch.runAll()
    setToast({ kind: 'ok', message: t.pdfToMd.success })
  }

  const onDownload = (item: BatchItem<PdfToMdResponse>) => {
    if (!item.result) return
    const out = item.file.name.replace(/\.pdf$/i, '.md')
    downloadText(out, item.result.md)
  }

  return (
    <div className="page container pdf2md-page">
      <header className="page__head">
        <h1>{t.pdfToMd.title}</h1>
        <p>{t.pdfToMd.subtitle}</p>
      </header>

      <div className="pdf2md">
        <div className="pdf2md__controls stack">
          <DropZone
            accept=".pdf,application/pdf"
            acceptLabel="PDF"
            onFiles={handleFiles}
            multiple
            disabled={batch.running}
          />
          <OptionsPanel
            legend={op.legend}
            fields={optionFields}
            values={options as Record<string, boolean | string | number>}
            onChange={onOption}
            disabled={batch.running}
          />
          <BatchPanel
            items={batch.items}
            running={batch.running}
            onConvertAll={onConvertAll}
            onClear={batch.clear}
            onRemove={batch.remove}
            onSkip={batch.skip}
            onDownload={onDownload}
            onDownloadAll={() => void zip.downloadZip(batch.items, t.batch.mdBundleName)}
            onSelect={(it) => setSelectedId(it.id)}
            selectedId={effectiveSelectedId}
            downloadLabel={t.pdfToMd.download}
            downloadBlocked={(it) => !!it.result?.warnings.includes('needs_ocr')}
            downloadAnywayLabel={t.pdfToMd.warnings.downloadAnyway}
          />
        </div>

        <div className="pdf2md__output stack">
          {ocrRequiredItem ? (
            <section className="alert alert--error" role="alert" aria-labelledby="ocr-required-h">
              <span className="alert__icon" aria-hidden="true">⚠</span>
              <div className="alert__body">
                <h2 id="ocr-required-h" className="alert__title" tabIndex={-1} ref={ocrErrorRef}>
                  {t.errors.ocrRequired.title}
                </h2>
                <p>{t.errors.ocrRequired.message}</p>
                <a
                  className="alert__cta"
                  href={OCR_DOCS_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {t.errors.ocrRequired.cta}
                  <span className="visually-hidden"> {t.errors.ocrRequired.ctaNewTab}</span>
                </a>
              </div>
            </section>
          ) : null}

          {!ocrRequiredItem && selectedWarnings.length ? (
            <section className="alert alert--warn" role="alert" aria-labelledby="warnings-h">
              <span className="alert__icon" aria-hidden="true">⚠</span>
              <div className="alert__body">
                <h2 id="warnings-h" className="alert__title">{t.pdfToMd.warnings.title}</h2>
                <ul className="alert__list">
                  {selectedWarnings.map((w, i) => {
                    // Backend emits short codes (`needs_ocr`,
                    // `images_not_persisted`); the dictionary translates the
                    // known ones and unknown codes fall back to the raw string.
                    const message = (t.pdfToMd.warnings as Record<string, string>)[w] ?? w
                    return <li key={i}>{message}</li>
                  })}
                </ul>
                {selectedWarnings.includes('needs_ocr') ? (
                  <p>{t.pdfToMd.warnings.downloadBlocked}</p>
                ) : null}
              </div>
            </section>
          ) : null}

          <DiagnosticPanel
            layout="strip"
            data={inspect.data}
            loading={inspect.status === 'loading'}
            error={inspect.status === 'error' ? inspect.error?.message : null}
          />

          <ComparePanes
            pdfUrl={pdfUrl}
            pdfName={selected?.file.name ?? null}
            markdown={selected?.result?.md ?? ''}
            sourceError={previewSourceError}
          />
        </div>
      </div>
      {toast && <Toast {...toast} onDismiss={() => setToast(null)} />}
    </div>
  )
}
