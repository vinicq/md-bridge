import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { BatchPanel } from '../components/BatchPanel'
import { Button } from '../components/Button'
import { ConvertButton } from '../components/ConvertButton'
import { DropZone } from '../components/DropZone'
import { MarkdownPreview } from '../components/MarkdownPreview'
import { ThemedPreview } from '../components/ThemedPreview'
import { DEFAULT_PAGE_SETUP } from '../components/pageSetup'
import { ThemePicker } from '../components/ThemePicker'
import { Toast } from '../components/Toast'
import { useBatchConvert, type BatchItem } from '../hooks/useBatchConvert'
import { useBatchZip } from '../hooks/useBatchZip'
import { useThemes } from '../hooks/useThemes'
import { useTranslation } from '../i18n'
import { convertMdToPdf } from '../lib/api'
import { readPrefs, writePrefs } from '../lib/prefs'

function initialTheme(): string {
  if (typeof window === 'undefined') return 'default'
  // The MD→PDF theme is the `defaultPdfTheme` in the unified prefs store (#64);
  // the preferences page edits the same value. readPrefs migrates the legacy
  // `md-bridge:md-to-pdf:theme` key.
  return readPrefs().defaultPdfTheme
}

export function MdToPdf() {
  const { t } = useTranslation()
  const [pasted, setPasted] = useState('')
  const [customCss, setCustomCss] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [toast, setToast] = useState<{ kind: 'ok' | 'warn'; message: string; id: number } | null>(
    null,
  )
  // Bumped per notification so <Toast> is keyed by identity: a replacement
  // toast remounts with a fresh timer, while parent re-renders keep the key
  // stable so the countdown is not reset (#355).
  const toastSeq = useRef(0)
  const { themes, status: themesStatus, error: themesError } = useThemes()
  // A `?theme=` query param (from the theme library's "Use theme", #392) wins at
  // mount over the persisted slug; the picker still owns it from there on.
  const [searchParams, setSearchParams] = useSearchParams()
  const [theme, setTheme] = useState<string>(() => searchParams.get('theme') || initialTheme())

  // Picking a theme in the UI takes over from the arrival `?theme=` param: drop
  // it so a later refresh honors the persisted pick, not the stale query.
  function pickTheme(slug: string): void {
    setTheme(slug)
    if (searchParams.has('theme')) {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev)
          next.delete('theme')
          return next
        },
        { replace: true },
      )
    }
  }

  // Reconcile the persisted slug against the server catalog (#356). A slug that
  // no longer exists (a renamed/removed theme or a stale localStorage value)
  // would leave the picker unselected and post an invalid theme to the API, so
  // fall back to default once the catalog is known. Derived rather than a
  // setState effect: no extra render, and the raw persisted value is left
  // intact so a theme that returns to the registry is honored again.
  const activeTheme =
    themesStatus === 'ready' && !themes.some((it) => it.slug === theme) ? 'default' : theme

  const batch = useBatchConvert<Blob>({
    // activeTheme is captured per render, so a run always uses the current
    // (reconciled) selection (#24); switching theme re-runs the queue via the
    // effect below.
    convert: (file, signal) =>
      convertMdToPdf(
        file,
        { theme: activeTheme, page_setup: DEFAULT_PAGE_SETUP, custom_css: customCss },
        signal,
      ),
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

  // Persist the picked theme so it survives a page reload (#24), now in the
  // unified prefs store (#64).
  useEffect(() => {
    if (typeof window !== 'undefined') writePrefs({ defaultPdfTheme: theme })
  }, [theme])

  // Re-run the queue when the effective theme changes so the preview reflects
  // the new theme without a manual re-click. Keying on activeTheme (not theme)
  // also heals the reconciliation race: if the catalog loads after a batch
  // already ran with a stale slug, activeTheme flips to default and the batch
  // re-runs with a valid theme (#356). Skip the first render and any run in
  // flight. Re-feeding the same File objects keeps the hook's single-pass model.
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
    // Only the effective theme drives this re-run; batch helpers are stable refs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTheme])

  // Pick up the latest completed item so the preview follows the run. Derived
  // during render so the user's explicit selection wins when it is still
  // valid, and the most recent successful conversion shows otherwise.
  const fallbackId = [...batch.items].reverse().find((it) => it.status === 'done')?.id ?? null
  const effectiveSelectedId =
    selectedId && batch.items.some((it) => it.id === selectedId) ? selectedId : fallbackId
  const selected = batch.items.find((it) => it.id === effectiveSelectedId) ?? null

  const handleFiles = (files: File[]) => batch.add(files)

  const onConvertAll = async () => {
    const summary = await batch.runAll()
    // Only claim success when a conversion actually succeeded. A failed batch
    // already shows the error on the row, so a green toast would contradict it
    // (#353); an empty run (nothing queued) shows nothing.
    if (summary.done > 0) setToast({ kind: 'ok', message: t.mdToPdf.success, id: (toastSeq.current += 1) })
  }

  const onConvertPasted = async () => {
    if (!pasted.trim()) return
    const file = new File([pasted], t.mdToPdf.pastedFilename, { type: 'text/markdown' })
    batch.add([file])
    // The newly-added item is queued; flush so runAll sees it.
    await Promise.resolve()
    const summary = await batch.runAll()
    if (summary.done > 0) setToast({ kind: 'ok', message: t.mdToPdf.success, id: (toastSeq.current += 1) })
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
        value={activeTheme}
        onChange={pickTheme}
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
          <details className="md-custom-css">
            <summary>{t.themeLib.custom}</summary>
            <p className="md-custom-css__hint">{t.themeLib.customHint}</p>
            <textarea
              className="md-input md-input--css"
              value={customCss}
              spellCheck={false}
              onChange={(e) => setCustomCss(e.target.value)}
              aria-label={t.themeLib.custom}
            />
          </details>
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
          ) : previewMarkdown ? (
            // Before a conversion, show the pasted Markdown styled by the selected
            // theme (default.css + overlay) so the theme's effect is visible live,
            // without a backend round-trip (#397).
            <ThemedPreview
              themeSlug={activeTheme}
              markdown={previewMarkdown}
              extraCss={customCss}
              title={t.mdToPdf.livePreviewTitle}
              className="pdf-preview"
            />
          ) : (
            <MarkdownPreview markdown={previewMarkdown} empty={t.mdToPdf.previewEmpty} />
          )}
        </div>
      </div>
      {toast && (
        <Toast
          key={toast.id}
          kind={toast.kind}
          message={toast.message}
          dismissLabel={t.toast.dismiss}
          onDismiss={() => setToast(null)}
        />
      )}
    </div>
  )
}
