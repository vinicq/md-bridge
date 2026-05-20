import { useState } from 'react'
import { BatchPanel } from '../components/BatchPanel'
import { Button } from '../components/Button'
import { ConvertButton } from '../components/ConvertButton'
import { DropZone } from '../components/DropZone'
import { MarkdownPreview } from '../components/MarkdownPreview'
import { Toast } from '../components/Toast'
import { useBatchConvert, type BatchItem } from '../hooks/useBatchConvert'
import { useTranslation } from '../i18n'
import { convertMdToPdf } from '../lib/api'

export function MdToPdf() {
  const { t } = useTranslation()
  const [pasted, setPasted] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [toast, setToast] = useState<{ kind: 'ok' | 'warn'; message: string } | null>(null)

  const batch = useBatchConvert<Blob>({
    convert: (file, signal) => convertMdToPdf(file, {}, signal),
    toBlobUrl: (blob) => URL.createObjectURL(blob),
  })

  // Pick up the latest completed item so the preview follows the run. Derived
  // during render so the user's explicit selection wins when it is still
  // valid, and the most recent successful conversion shows otherwise.
  const fallbackId = [...batch.items].reverse().find((it) => it.status === 'done')?.id ?? null
  const effectiveSelectedId =
    selectedId && batch.items.some((it) => it.id === selectedId) ? selectedId : fallbackId
  const selected = batch.items.find((it) => it.id === effectiveSelectedId) ?? null

  const handleFiles = (files: File[]) => batch.add(files)

  const onConvertAll = async () => {
    await batch.runAll()
    setToast({ kind: 'ok', message: t.mdToPdf.success })
  }

  const onConvertPasted = async () => {
    if (!pasted.trim()) return
    const file = new File([pasted], t.mdToPdf.pastedFilename, { type: 'text/markdown' })
    batch.add([file])
    // The newly-added item is queued; flush so runAll sees it.
    await Promise.resolve()
    await batch.runAll()
    setToast({ kind: 'ok', message: t.mdToPdf.success })
  }

  const onDownload = (item: BatchItem<Blob>) => {
    if (!item.blobUrl) return
    const out = item.file.name.replace(/\.md$/i, '') + '.pdf'
    const a = document.createElement('a')
    a.href = item.blobUrl
    a.download = out
    document.body.appendChild(a)
    a.click()
    a.remove()
  }

  const previewMarkdown = pasted.trim()
  const previewUrl = selected?.blobUrl ?? null

  return (
    <div className="page container">
      <header className="page__head">
        <h1>{t.mdToPdf.title}</h1>
        <p>{t.mdToPdf.subtitle}</p>
      </header>

      <div className="grid-2">
        <div className="stack">
          <DropZone
            accept=".md,text/markdown"
            acceptLabel="Markdown"
            onFiles={handleFiles}
            multiple
            disabled={batch.running}
          />
          <textarea
            className="md-input"
            placeholder={t.mdToPdf.paste}
            value={pasted}
            onChange={(e) => setPasted(e.target.value)}
            aria-label={t.mdToPdf.pasteLabel}
          />
          <div className="stack__actions">
            <ConvertButton
              status={batch.running ? 'loading' : 'idle'}
              onClick={pasted.trim() ? onConvertPasted : onConvertAll}
              disabled={!pasted.trim() && batch.items.length === 0}
              labels={{
                idle: t.mdToPdf.generate,
                loading: t.mdToPdf.generating,
                success: t.mdToPdf.success,
                error: t.mdToPdf.generate,
              }}
            />
            {selected?.blobUrl && (
              <Button variant="ghost" onClick={() => onDownload(selected)}>
                {t.mdToPdf.download}
              </Button>
            )}
          </div>

          <BatchPanel
            items={batch.items}
            running={batch.running}
            onConvertAll={onConvertAll}
            onClear={batch.clear}
            onRemove={batch.remove}
            onDownload={onDownload}
            onSelect={(it) => setSelectedId(it.id)}
            selectedId={effectiveSelectedId}
            downloadLabel={t.mdToPdf.download}
          />
        </div>

        <div>
          {previewUrl ? (
            <iframe title={t.mdToPdf.title} src={previewUrl} className="pdf-preview" />
          ) : (
            <MarkdownPreview markdown={previewMarkdown} empty={t.mdToPdf.previewEmpty} />
          )}
        </div>
      </div>
      {toast && <Toast {...toast} onDismiss={() => setToast(null)} />}
    </div>
  )
}
