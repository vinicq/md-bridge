import { useEffect, useRef, useState } from 'react'
import { BatchPanel } from '../components/BatchPanel'
import { DropZone } from '../components/DropZone'
import { MarkdownPreview } from '../components/MarkdownPreview'
import { OptionsPanel, type OptionField } from '../components/OptionsPanel'
import { Toast } from '../components/Toast'
import { useBatchConvert, type BatchItem } from '../hooks/useBatchConvert'
import { useBatchZip } from '../hooks/useBatchZip'
import { useInspect } from '../hooks/useInspect'
import { useTranslation } from '../i18n'
import { convertPdfToMd, type PdfToMdOptions, type PdfToMdResponse } from '../lib/api'
import { DiagnosticPanel } from '../components/DiagnosticPanel'

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

  // Auto-select the most recently finished item so the preview follows the
  // run. Derived during render so the user's explicit selection wins when it
  // is still valid, and the most recent successful conversion shows otherwise.
  const fallbackId = [...batch.items].reverse().find((it) => it.status === 'done')?.id ?? null
  const effectiveSelectedId =
    selectedId && batch.items.some((it) => it.id === selectedId) ? selectedId : fallbackId

  // Run inspect on the first file so the diagnostic panel still has something
  // to show (helps the user judge if OCR is needed before kicking off the run).
  const firstName = batch.items[0]?.file.name
  useEffect(() => {
    const first = batch.items[0]?.file
    if (first) void inspect.run(first)
    else inspect.reset()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [firstName])

  const selected = batch.items.find((it) => it.id === effectiveSelectedId) ?? null

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
    <div className="page container">
      <header className="page__head">
        <h1>{t.pdfToMd.title}</h1>
        <p>{t.pdfToMd.subtitle}</p>
      </header>

      <div className="grid-2">
        <div className="stack">
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
          <DiagnosticPanel
            data={inspect.data}
            loading={inspect.status === 'loading'}
            error={inspect.status === 'error' ? inspect.error?.message : null}
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

        <div>
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

          <MarkdownPreview
            markdown={selected?.result?.md ?? ''}
            empty={t.pdfToMd.previewEmpty}
          />

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
        </div>
      </div>
      {toast && <Toast {...toast} onDismiss={() => setToast(null)} />}
    </div>
  )
}
