import { useState } from 'react'
import { BatchPanel } from '../components/BatchPanel'
import { Button } from '../components/Button'
import { ConvertButton } from '../components/ConvertButton'
import { DropZone } from '../components/DropZone'
import { MarkdownPreview } from '../components/MarkdownPreview'
import { Toast } from '../components/Toast'
import { useBatchConvert, type BatchItem } from '../hooks/useBatchConvert'
import { useBatchZip } from '../hooks/useBatchZip'
import { useTranslation } from '../i18n'
import { convertMdToDocx } from '../lib/api'

// Markdown → DOCX page (#276). Mirrors MdToPdf, minus the theme picker, the
// page-setup panel, and the result preview: the DOCX converter takes no
// tunables and a .docx cannot render in an iframe. Per the locked design
// contract the right pane previews the INPUT markdown in every state, never the
// result. Do not "fix" this by re-adding an iframe; there is nothing to embed.
export function MdToDocx() {
  const { t } = useTranslation()
  const [pasted, setPasted] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [toast, setToast] = useState<{ kind: 'ok' | 'warn'; message: string } | null>(null)

  const batch = useBatchConvert<Blob>({
    convert: (file, signal) => convertMdToDocx(file, {}, signal),
    toBlobUrl: (blob) => URL.createObjectURL(blob),
    // 10-minute ceiling so a backgrounded tab cannot leave an item stuck in
    // flight forever (issue #138).
    convertTimeoutMs: 10 * 60 * 1000,
  })
  const zip = useBatchZip<Blob>({
    toEntry: async (it) => ({
      name: it.file.name.replace(/\.md$/i, '') + '.docx',
      data: new Uint8Array(await (it.result as Blob).arrayBuffer()),
    }),
  })

  const fallbackId = [...batch.items].reverse().find((it) => it.status === 'done')?.id ?? null
  const effectiveSelectedId =
    selectedId && batch.items.some((it) => it.id === selectedId) ? selectedId : fallbackId

  const handleFiles = (files: File[]) => batch.add(files)

  const onConvertAll = async () => {
    await batch.runAll()
    setToast({ kind: 'ok', message: t.mdToDocx.success })
  }

  const onConvertPasted = async () => {
    if (!pasted.trim()) return
    const file = new File([pasted], t.mdToDocx.pastedFilename, { type: 'text/markdown' })
    batch.add([file])
    // The newly-added item is queued; flush so runAll sees it.
    await Promise.resolve()
    await batch.runAll()
    setToast({ kind: 'ok', message: t.mdToDocx.success })
  }

  const onDownload = (item: BatchItem<Blob>) => {
    if (!item.blobUrl) return
    const out = item.file.name.replace(/\.md$/i, '') + '.docx'
    const a = document.createElement('a')
    a.href = item.blobUrl
    a.download = out
    document.body.appendChild(a)
    a.click()
    a.remove()
  }

  const selected = batch.items.find((it) => it.id === effectiveSelectedId) ?? null
  const previewMarkdown = pasted.trim()

  return (
    <div className="page container">
      <header className="page__head">
        <h1>{t.mdToDocx.title}</h1>
        <p>{t.mdToDocx.subtitle}</p>
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
            placeholder={t.mdToDocx.paste}
            value={pasted}
            onChange={(e) => setPasted(e.target.value)}
            aria-label={t.mdToDocx.pasteLabel}
          />
          <div className="stack__actions">
            <ConvertButton
              status={batch.running ? 'loading' : 'idle'}
              onClick={pasted.trim() ? onConvertPasted : onConvertAll}
              disabled={!pasted.trim() && batch.items.length === 0}
              labels={{
                idle: t.mdToDocx.generate,
                loading: t.mdToDocx.generating,
                success: t.mdToDocx.success,
                error: t.mdToDocx.generate,
              }}
            />
            {selected?.blobUrl && (
              <Button variant="ghost" onClick={() => onDownload(selected)}>
                {t.mdToDocx.download}
              </Button>
            )}
          </div>

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
            onDownloadAll={() => void zip.downloadZip(batch.items, t.batch.docxBundleName)}
            onSelect={(it) => setSelectedId(it.id)}
            selectedId={effectiveSelectedId}
            downloadLabel={t.mdToDocx.download}
          />
        </div>

        <div>
          {/* Always the INPUT preview; a .docx has no in-browser preview. */}
          <MarkdownPreview markdown={previewMarkdown} empty={t.mdToDocx.previewEmpty} />
        </div>
      </div>
      {toast && <Toast {...toast} onDismiss={() => setToast(null)} />}
    </div>
  )
}
