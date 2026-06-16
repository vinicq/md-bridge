import { useEffect, useRef, useState } from 'react'
import { BatchPanel } from '../components/BatchPanel'
import { DiagnosticPanel } from '../components/DiagnosticPanel'
import { DropZone } from '../components/DropZone'
import { MarkdownPreview } from '../components/MarkdownPreview'
import { Toast } from '../components/Toast'
import { useBatchConvert, type BatchItem } from '../hooks/useBatchConvert'
import { useBatchZip } from '../hooks/useBatchZip'
import { useInspect } from '../hooks/useInspect'
import { useTranslation } from '../i18n'
import { convertPdfToMd, type PdfToMdResponse } from '../lib/api'
import { stripFrontmatter } from '../lib/stripFrontmatter'
import './PdfToMd.css'

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

  const batch = useBatchConvert<PdfToMdResponse>({
    convert: (file, signal) => convertPdfToMd(file, {}, signal),
    convertTimeoutMs: 10 * 60 * 1000,
  })
  const inspect = useInspect()
  const zip = useBatchZip<PdfToMdResponse>({
    toEntry: (it) => ({
      name: it.file.name.replace(/\.pdf$/i, '.md'),
      data: new TextEncoder().encode(it.result?.md ?? ''),
    }),
  })

  const lastDoneId = [...batch.items].reverse().find((it) => it.status === 'done')?.id ?? null
  const previewFallbackId = lastDoneId ?? batch.items[0]?.id ?? null
  const effectiveSelectedId =
    selectedId && batch.items.some((it) => it.id === selectedId) ? selectedId : previewFallbackId

  const selected = batch.items.find((it) => it.id === effectiveSelectedId) ?? null

  useEffect(() => {
    if (selected?.file) void inspect.run(selected.file)
    else inspect.reset()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [effectiveSelectedId])

  const ocrRequiredItem = batch.items.find(
    (it) => it.status === 'error' && it.error?.code === 'ocr_required',
  )
  const ocrErrorRef = useRef<HTMLHeadingElement>(null)
  useEffect(() => {
    if (ocrRequiredItem) ocrErrorRef.current?.focus()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ocrRequiredItem?.id])

  const selectedWarnings = selected?.result?.warnings ?? []

  const handleFiles = (files: File[]) => batch.add(files)

  const onConvertAll = async () => {
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
          <BatchPanel
            items={batch.items}
            running={batch.running}
            onConvertAll={onConvertAll}
            onClear={batch.clear}
            onRemove={batch.remove}
            onMove={batch.move}
            onMoveTo={batch.moveTo}
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

          <section className="md-output" aria-label={t.pdfToMd.previewLabel}>
            <MarkdownPreview
              markdown={stripFrontmatter(selected?.result?.md ?? '')}
              empty={t.pdfToMd.previewEmpty}
            />
          </section>
        </div>
      </div>
      {toast && <Toast {...toast} onDismiss={() => setToast(null)} />}
    </div>
  )
}
