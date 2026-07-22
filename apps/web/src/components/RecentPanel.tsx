import { useState } from 'react'
import { useTranslation } from '../i18n'
import { formatSize } from '../lib/formatSize'
import type { HistoryEntry } from '../lib/history'
import { Button } from './Button'
import './RecentPanel.css'

interface RecentPanelProps {
  entries: HistoryEntry[]
  isLive: (entry: HistoryEntry) => boolean
  onRedownload: (entry: HistoryEntry) => void
  onRerun: (entry: HistoryEntry) => void
  onClear: () => void
}

type RowStatus = 'done' | 'warn' | 'expired'

function rowStatus(entry: HistoryEntry, live: boolean): RowStatus {
  if (entry.outcome === 'needs_ocr') return 'warn'
  return live ? 'done' : 'expired'
}

export function RecentPanel({
  entries,
  isLive,
  onRedownload,
  onRerun,
  onClear,
}: RecentPanelProps) {
  const { t } = useTranslation()
  const h = t.history
  // Snapshot "now" once at mount: ages are coarse (m/h ago), so a per-render
  // clock read is both needless and impure during render.
  const [now] = useState(() => Date.now())

  function ageOf(createdAt: number): string {
    const minutes = Math.floor((now - createdAt) / 60_000)
    return minutes < 60 ? h.ageMinutes(minutes) : h.ageHours(Math.floor(minutes / 60))
  }

  const statusLabel: Record<RowStatus, string> = {
    done: h.statusDone,
    warn: h.statusWarn,
    expired: h.statusExpired,
  }

  return (
    <section className="recent" aria-label={h.title}>
      <div className="recent__head">
        <h3 className="recent__title">{h.title}</h3>
        {entries.length > 0 && (
          <div className="recent__head-right">
            <span className="recent__count">{h.count(entries.length)}</span>
            <Button variant="ghost" className="recent__clear" onClick={onClear}>
              {h.clearAll}
            </Button>
          </div>
        )}
      </div>

      {entries.length === 0 ? (
        <p className="recent__empty">{h.empty}</p>
      ) : (
        <ul className="recent__list">
          {entries.map((entry) => {
            const live = isLive(entry)
            const status = rowStatus(entry, live)
            const ext = entry.pair === 'pdf-to-md' ? '.md' : '.pdf'
            return (
              <li key={entry.id} className={`recent-row recent-row--${status}`}>
                <div className="recent-row__name">
                  <b>{entry.name}</b>
                  <small>
                    {formatSize(entry.size)}
                    {entry.pages != null && ` · ${h.pages(entry.pages)}`}
                    {entry.options.theme && ` · ${entry.options.theme}`}
                    {` · ${ageOf(entry.createdAt)}`}
                  </small>
                </div>
                <div className="recent-row__actions">
                  <span className={`recent-badge recent-badge--${status}`}>
                    {statusLabel[status]}
                  </span>
                  {/* needs_ocr yields no usable Markdown, so it is never
                      re-downloadable (mirrors BatchPanel's downloadBlocked). */}
                  {live && entry.outcome === 'done' && (
                    <Button
                      variant="ghost"
                      className="recent-row__btn"
                      aria-label={h.redownloadLabel(entry.name)}
                      onClick={() => onRedownload(entry)}
                    >
                      {h.redownload(ext)}
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    className="recent-row__btn"
                    aria-label={h.rerunLabel(entry.name)}
                    onClick={() => onRerun(entry)}
                  >
                    {h.rerun}
                  </Button>
                </div>
              </li>
            )
          })}
        </ul>
      )}

      <p className="recent__privacy">{h.privacy}</p>
    </section>
  )
}
