import { useTranslation } from '../i18n'
import type { BatchItem } from '../hooks/useBatchConvert'
import { Button } from './Button'
import { Spinner } from './Spinner'
import './BatchPanel.css'

interface BatchPanelProps<TResult> {
  items: BatchItem<TResult>[]
  running: boolean
  onConvertAll: () => void
  onClear: () => void
  onRemove: (id: string) => void
  /** Called when the user skips an item that is still converting. */
  onSkip?: (id: string) => void
  /** Called when the user clicks the per-item download button. */
  onDownload: (item: BatchItem<TResult>) => void
  /** Called when the user clicks "Download all"; only rendered when provided. */
  onDownloadAll?: () => void
  /** Optional: select an item to drive the right-side preview panel. */
  onSelect?: (item: BatchItem<TResult>) => void
  selectedId?: string | null
  /** Label of the per-item download button (e.g. ".md" or ".pdf"). */
  downloadLabel: string
  /** When it returns true for a done item, the download is reframed as an
   *  explicit "download anyway" escape (e.g. a near-empty needs_ocr result). */
  downloadBlocked?: (item: BatchItem<TResult>) => boolean
  /** Label used in place of downloadLabel when downloadBlocked returns true. */
  downloadAnywayLabel?: string
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

export function BatchPanel<TResult>({
  items,
  running,
  onConvertAll,
  onClear,
  onRemove,
  onSkip,
  onDownload,
  onDownloadAll,
  onSelect,
  selectedId,
  downloadLabel,
  downloadBlocked,
  downloadAnywayLabel,
}: BatchPanelProps<TResult>) {
  const { t } = useTranslation()
  if (items.length === 0) return null

  // The hook leaves timeout/skip errors with an empty message and only a code,
  // so the localized text lives here rather than in the hook.
  const errorText = (error: { code: string; message: string }): string => {
    if (error.code === 'timeout') return t.batch.errorTimeout
    if (error.code === 'skipped') return t.batch.errorSkipped
    return error.message
  }

  const done = items.filter((it) => it.status === 'done').length
  const hasQueued = items.some((it) => it.status === 'queued')
  const hasDone = done > 0

  return (
    <div className="batch">
      <header className="batch__head">
        <strong>{t.batch.heading(items.length)}</strong>
        <span className="batch__progress" aria-live="polite">{t.batch.progress(done, items.length)}</span>
      </header>

      <ul className="batch__list">
        {items.map((item) => {
          const isSelected = item.id === selectedId
          return (
            <li
              key={item.id}
              className={`batch__row batch__row--${item.status} ${isSelected ? 'is-selected' : ''}`.trim()}
            >
              <button
                type="button"
                className="batch__file"
                onClick={() => onSelect?.(item)}
                title={item.file.name}
              >
                <span className="batch__name">{item.file.name}</span>
                <span className="batch__size">{formatSize(item.file.size)}</span>
              </button>

              <span className={`batch__status batch__status--${item.status}`}>
                {item.status === 'converting' && <Spinner size={14} label={t.batch.statusConverting} />}
                {item.status === 'queued' && t.batch.statusQueued}
                {item.status === 'converting' && t.batch.statusConverting}
                {item.status === 'done' && t.batch.statusDone}
                {item.status === 'error' && t.batch.statusError}
              </span>

              <div className="batch__actions">
                {item.status === 'done' && (
                  <Button variant="ghost" onClick={() => onDownload(item)}>
                    {downloadBlocked?.(item) ? (downloadAnywayLabel ?? downloadLabel) : downloadLabel}
                  </Button>
                )}
                {item.status === 'converting' && onSkip && (
                  <Button
                    variant="ghost"
                    onClick={() => onSkip(item.id)}
                    aria-label={t.batch.skipLabel(item.file.name)}
                  >
                    {t.batch.skip}
                  </Button>
                )}
                <Button
                  variant="icon"
                  onClick={() => onRemove(item.id)}
                  aria-label={`remove ${item.file.name}`}
                >
                  ×
                </Button>
              </div>

              {item.error && (
                <p className="batch__error" role="alert">
                  {errorText(item.error)}
                </p>
              )}
            </li>
          )
        })}
      </ul>

      <footer className="batch__foot">
        <Button onClick={onConvertAll} disabled={!hasQueued || running} loading={running}>
          {t.batch.convertAll}
        </Button>
        {hasDone && onDownloadAll && (
          <Button variant="ghost" onClick={onDownloadAll} disabled={running}>
            {t.batch.downloadAll(done)}
          </Button>
        )}
        <Button variant="ghost" onClick={onClear} disabled={running}>
          {t.batch.clear}
        </Button>
        {hasDone && (
          <span className="batch__hint">
            {t.batch.progress(done, items.length)}
          </span>
        )}
      </footer>
    </div>
  )
}
