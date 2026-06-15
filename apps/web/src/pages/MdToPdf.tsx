import { useEffect, useRef, useState } from 'react'
import { BatchPanel } from '../components/BatchPanel'
import { Button } from '../components/Button'
import { ConvertButton } from '../components/ConvertButton'
import { DropZone } from '../components/DropZone'
import { MarkdownPreview } from '../components/MarkdownPreview'
import { DEFAULT_PAGE_SETUP } from '../components/pageSetup'
import { ThemePicker } from '../components/ThemePicker'
import { Toast } from '../components/Toast'
import { useBatchConvert, type BatchItem } from '../hooks/useBatchConvert'
import { useBatchZip } from '../hooks/useBatchZip'
import { useThemes } from '../hooks/useThemes'
import { useTranslation } from '../i18n'
import { convertMdToPdf } from '../lib/api'

const THEME_STORAGE_KEY = 'md-bridge:md-to-pdf:theme'

function initialTheme(): string {
  if (typeof window === 'undefined') return 'default'
  return window.localStorage.getItem(THEME_STORAGE_KEY) || 'default'
}

export function MdToPdf() {
  const { t } = useTranslation()
  const [pasted, setPasted] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [toast, setToast] = useState<{ kind: 'ok' | 'warn'; message: string } | null>(null)
  const { themes, status: themesStatus, error: themesError } = useThemes()
  const [theme, setTheme] = useState<string>(initialTheme)

  const batch = useBatchConvert<Blob>({
    // The theme is captured per render, so a run always uses the current
    // selection (#24); switching theme re-runs the queue via the effect below.
    convert: (file, signal) => convertMdToPdf(file, { theme, page_setup: DEFAULT_PAGE_SETUP }, signal),
    toBlobUrl: (blob) => URL.createObjectURL(blob),
    // 10-minute ceiling so a backgrounded tab cannot leave an item stuck in
    // flight forever (issue #138). Removing this line restores the old
    // no-timeout behavior.
    convertTimeoutMs: 10 * 60 * 1000,
  })
  const zip = useBatchZip<Blob>({
    toEntry: async (it) => ({
      name: it.file.name.replace(/\.md$/i, '') + '.pdf',
      data: new Uint8Array(await (it.result as Blob).arrayBuffer()),
    }),
  })

  // Persist the picked theme so it survives a page reload (#24).
  useEffect(() => {
    if (typeof window !== 'undefined') window.localStorage.setItem(THEME_STORAGE_KEY, theme)
  }, [theme])

  // Re-run the queue when the theme changes so the preview reflects the new
  // theme without a manual re-click. Skip the first render (initial mount) and
  // any run in flight. Re-feeding the same File objects keeps the hook's
  // single-pass model untouched.
  const didMount = useRef(false)
  useEffect(() => {
    if (!didMount.current) {
      didMount.current = true
      return
    }
    const files = batch.items.map((it) => it.file)
    if (files.length === 0 || batch.running) return
    batch.clear()
    batch.add(files)
    void (async () => {
      await Promise.resolve()
      await batch.runAll()
    })()
    // Only the theme drives this re-run; batch helpers are stable refs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [theme])

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

      <ThemePicker
        themes={themes}
        value={theme}
        onChange={setTheme}
        label={t.themePicker.label}
        loadingLabel={t.themePicker.loading}
        disabled={batch.running}
        loading={themesStatus === 'loading'}
        loadError={themesStatus === 'error' ? (themesError ?? t.themePicker.loadError) : null}
      />

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
            onMove={batch.move}
            onMoveTo={batch.moveTo}
            onSkip={batch.skip}
            onDownload={onDownload}
            onDownloadAll={() => void zip.downloadZip(batch.items, t.batch.pdfBundleName)}
            onSelect={(it) => setSelectedId(it.id)}
            selectedId={effectiveSelectedId}
            downloadLabel={t.mdToPdf.download}
          />
        </div>

        <div>
          {previewUrl ? (
            <iframe title={t.mdToPdf.previewIframeTitle} src={previewUrl} className="pdf-preview" />
          ) : (
            <MarkdownPreview markdown={previewMarkdown} empty={t.mdToPdf.previewEmpty} />
          )}
        </div>
      </div>
      {toast && <Toast {...toast} onDismiss={() => setToast(null)} />}
    </div>
  )
}
