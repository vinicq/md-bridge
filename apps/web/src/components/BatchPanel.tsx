import { useState, type DragEvent, type KeyboardEvent } from 'react'
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
  onMove: (id: string, direction: -1 | 1) => void
  onMoveTo: (id: string, targetId: string) => void
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
  onMove,
  onMoveTo,
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
  const [draggedId, setDraggedId] = useState<string | null>(null)
  const [dropTargetId, setDropTargetId] = useState<string | null>(null)
  const [grabbedId, setGrabbedId] = useState<string | null>(null)
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
  const canReorder = !running && items.length > 1

  const move = (id: string, direction: -1 | 1) => {
    if (!canReorder) return
    onMove(id, direction)
  }

  const handleDragStart = (event: DragEvent<HTMLButtonElement>, id: string) => {
    if (!canReorder) {
      event.preventDefault()
      return
    }
    setDraggedId(id)
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', id)
  }

  const handleDrop = (event: DragEvent<HTMLLIElement>, targetId: string) => {
    event.preventDefault()
    if (!canReorder) return
    const sourceId = draggedId ?? event.dataTransfer.getData('text/plain')
    if (sourceId && sourceId !== targetId) onMoveTo(sourceId, targetId)
    setDraggedId(null)
    setDropTargetId(null)
  }

  const handleRowKeyDown = (event: KeyboardEvent<HTMLLIElement>, id: string) => {
    if (event.currentTarget !== event.target) return
    if (!canReorder) return

    if (event.altKey && event.key === 'ArrowUp') {
      event.preventDefault()
      move(id, -1)
      return
    }
    if (event.altKey && event.key === 'ArrowDown') {
      event.preventDefault()
      move(id, 1)
      return
    }
    if (event.key === ' ') {
      event.preventDefault()
      setGrabbedId((prev) => (prev === id ? null : id))
      return
    }
    if (grabbedId === id && event.key === 'ArrowUp') {
      event.preventDefault()
      move(id, -1)
      return
    }
    if (grabbedId === id && event.key === 'ArrowDown') {
      event.preventDefault()
      move(id, 1)
    }
  }

  return (
    <div className="batch">
      <header className="batch__head">
        <strong>{t.batch.heading(items.length)}</strong>
        <span className="batch__progress" aria-live="polite">{t.batch.progress(done, items.length)}</span>
      </header>

      <ul className="batch__list">
        {items.map((item, index) => {
          const isSelected = item.id === selectedId
          const isDragged = item.id === draggedId
          const isDropTarget = item.id === dropTargetId
          const isGrabbed = item.id === grabbedId
          const rowClass = [
            'batch__row',
            `batch__row--${item.status}`,
            isSelected ? 'is-selected' : '',
            isDragged ? 'is-dragging' : '',
            isDropTarget ? 'is-drop-target' : '',
            isGrabbed ? 'is-grabbed' : '',
          ].filter(Boolean).join(' ')
          return (
            <li
              key={item.id}
              className={rowClass}
              tabIndex={0}
              aria-grabbed={isGrabbed}
              onKeyDown={(event) => handleRowKeyDown(event, item.id)}
              onDragOver={(event) => {
                if (!canReorder) return
                event.preventDefault()
                event.dataTransfer.dropEffect = 'move'
                setDropTargetId(item.id)
              }}
              onDragLeave={() => setDropTargetId((current) => (current === item.id ? null : current))}
              onDrop={(event) => handleDrop(event, item.id)}
            >
              <button
                type="button"
                className="batch__drag"
                draggable={canReorder}
                aria-disabled={!canReorder}
                aria-label={t.batch.dragLabel(item.file.name)}
                title={t.batch.dragLabel(item.file.name)}
                onDragStart={(event) => handleDragStart(event, item.id)}
                onDragEnd={() => {
                  setDraggedId(null)
                  setDropTargetId(null)
                }}
                onClick={() => {
                  if (canReorder) setGrabbedId((prev) => (prev === item.id ? null : item.id))
                }}
                disabled={!canReorder}
              >
                <span aria-hidden="true">::</span>
              </button>

              <button
                type="button"
                className="batch__file"
                onClick={() => onSelect?.(item)}
                title={item.file.name}
              >
                <span className="batch__name">{item.file.name}</span>
              </button>

              <div className="batch__meta">
                <span className={`batch__status batch__status--${item.status}`}>
                  {item.status === 'converting' && <Spinner size={14} label={t.batch.statusConverting} />}
                  {item.status === 'queued' && t.batch.statusQueued}
                  {item.status === 'converting' && <span aria-hidden="true">{t.batch.statusConverting}</span>}
                  {item.status === 'done' && t.batch.statusDone}
                  {item.status === 'error' && t.batch.statusError}
                </span>
                <span className="batch__size">{formatSize(item.file.size)}</span>
              </div>

              <div className="batch__actions">
                <Button
                  variant="icon"
                  onClick={() => onRemove(item.id)}
                  aria-label={`remove ${item.file.name}`}
                >
                  ×
                </Button>
                <Button
                  variant="icon"
                  onClick={() => move(item.id, -1)}
                  disabled={!canReorder || index === 0}
                  aria-label={`move ${item.file.name} up`}
                >
                  Up
                </Button>
                <Button
                  variant="icon"
                  onClick={() => move(item.id, 1)}
                  disabled={!canReorder || index === items.length - 1}
                  aria-label={`move ${item.file.name} down`}
                >
                  Down
                </Button>
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
