import { useEffect, useState } from 'react'
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
  /** A batch is running: Re-run would only queue silently, so it is disabled. */
  busy?: boolean
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
  busy = false,
}: RecentPanelProps) {
  const { t } = useTranslation()
  const h = t.history
  // A clock in state, refreshed each minute: reading Date.now() during render is
  // impure, and a mount-time snapshot both goes stale and can read slightly
  // behind a just-recorded entry's timestamp (clamped to 0 below).
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 60_000)
    return () => clearInterval(id)
  }, [])

  function ageOf(createdAt: number): string {
    const minutes = Math.max(0, Math.floor((now - createdAt) / 60_000))
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
                    disabled={busy}
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
