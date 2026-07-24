import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { BatchPanel } from '../components/BatchPanel'
import { Button } from '../components/Button'
import { ConvertButton } from '../components/ConvertButton'
import { DropZone } from '../components/DropZone'
import { MarkdownPreview } from '../components/MarkdownPreview'
import { PresetChips } from '../components/PresetChips'
import { SettingRow } from '../components/SettingRow'
import { Switch } from '../components/Switch'
import { ThemedPreview } from '../components/ThemedPreview'
import { DEFAULT_PAGE_SETUP } from '../components/pageSetup'
import { ThemePicker } from '../components/ThemePicker'
import { Toast } from '../components/Toast'
import { useBatchConvert, type BatchItem } from '../hooks/useBatchConvert'
import { useBatchZip } from '../hooks/useBatchZip'
import { usePresets } from '../hooks/usePresets'
import { useThemes } from '../hooks/useThemes'
import { useTranslation } from '../i18n'
import { convertMdToPdf } from '../lib/api'
import { parseImport, serializePresets, type Preset } from '../lib/presets'
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
  // Opt-in Mermaid rendering (#439). Default off keeps today's behavior: a
  // ```mermaid fence stays a code block unless the user turns this on.
  const [renderMermaid, setRenderMermaid] = useState(false)
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
  const presets = usePresets('md-to-pdf')
  const [activePresetId, setActivePresetId] = useState<string | null>(null)
  // Bumped on each preset apply so the re-run effect fires even when the preset
  // changes only the custom CSS (theme unchanged), keeping preview and download
  // in sync with the active preset.
  const [applyTick, setApplyTick] = useState(0)

  // Picking a theme in the UI takes over from the arrival `?theme=` param: drop
  // it so a later refresh honors the persisted pick, not the stale query.
  function pickTheme(slug: string): void {
    setTheme(slug)
    // A manual theme change diverges from any applied preset, so drop the marker.
    setActivePresetId(null)
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
        {
          theme: activeTheme,
          page_setup: DEFAULT_PAGE_SETUP,
          custom_css: customCss,
          render_mermaid: renderMermaid,
        },
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
    // Only refresh a batch that already produced a result. A purely-queued batch
    // (files dropped, never converted) must wait for the explicit Convert button,
    // so toggling an option does not silently start the upload/conversion (#464).
    if (!batch.items.some((it) => it.status === 'done' || it.status === 'error')) return
    batch.clear()
    batch.add(files)
    void (async () => {
      await Promise.resolve()
      await batch.runAll()
    })()
    // Re-run on an effective-theme change, a preset apply (applyTick), or the
    // Mermaid toggle, so a CSS-only preset or a toggled option does not leave a
    // stale PDF. One effect keyed on all three, so a preset that also changes
    // the theme still re-runs exactly once. Batch helpers are stable refs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTheme, applyTick, renderMermaid])

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

  // Presets bundle the editable md-to-pdf options (today: theme + custom CSS).
  // Applying one re-uses the existing theme re-run effect; no new wiring.
  const applyPreset = (preset: Preset) => {
    // Route through pickTheme so the theme is set and the stale ?theme= arrival
    // query is cleared; it also clears the marker, which we re-set below.
    pickTheme(preset.options.theme ?? 'default')
    setCustomCss(preset.options.custom_css ?? '')
    setActivePresetId(preset.id)
    setApplyTick((t) => t + 1)
  }

  const savePreset = (name: string) => {
    const preset: Preset = {
      id: `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`,
      name,
      pair: 'md-to-pdf',
      options: { theme: activeTheme, custom_css: customCss },
      createdAt: Date.now(),
    }
    if (presets.save(preset)) setActivePresetId(preset.id)
  }

  const deletePreset = (id: string) => {
    presets.remove(id)
    if (activePresetId === id) setActivePresetId(null)
  }

  const importPresetsFile = (file: File) => {
    const reader = new FileReader()
    reader.onload = () => {
      const parsed = parseImport(String(reader.result))
      if (!parsed) {
        setToast({ kind: 'warn', message: t.presets.importInvalid, id: (toastSeq.current += 1) })
        return
      }
      const result = presets.importFrom(parsed)
      setToast({
        kind: 'ok',
        message: t.presets.imported(result.imported, result.ignored),
        id: (toastSeq.current += 1),
      })
    }
    reader.onerror = () =>
      setToast({ kind: 'warn', message: t.presets.readError, id: (toastSeq.current += 1) })
    reader.readAsText(file)
  }

  const exportPresets = () => {
    const blob = new Blob([serializePresets('md-to-pdf')], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'md-bridge-presets.json'
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  const previewMarkdown = pasted.trim()
  const previewUrl = selected?.blobUrl ?? null

  return (
    <div className="page container">
      <header className="page__head">
        <h1>{t.mdToPdf.title}</h1>
        <p>{t.mdToPdf.subtitle}</p>
      </header>

      <PresetChips
        presets={presets.presets}
        activeId={activePresetId}
        atCap={presets.atCap}
        onApply={applyPreset}
        onDelete={deletePreset}
        onSave={savePreset}
        onImport={importPresetsFile}
        onExport={exportPresets}
        busy={batch.running}
      />

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

      <div className="md-options">
        <SettingRow
          label={t.mdToPdf.renderMermaid}
          hint={t.mdToPdf.renderMermaidHint}
          hintId="md-mermaid-hint"
          control={
            <Switch
              checked={renderMermaid}
              onChange={setRenderMermaid}
              label={t.mdToPdf.renderMermaid}
              onText={t.preferences.on}
              offText={t.preferences.off}
              describedBy="md-mermaid-hint"
              disabled={batch.running}
            />
          }
        />
      </div>

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
              onChange={(e) => {
                setCustomCss(e.target.value)
                // Editing the CSS diverges from any applied preset.
                setActivePresetId(null)
              }}
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
