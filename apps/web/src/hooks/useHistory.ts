/* React binding over the history store (#63). The persisted list holds only
 * metadata; the result blobs and source files live in a session-scoped registry
 * (empty after a reload), so a row is "live" only while its blob is in this tab
 * and within the 24h window. */
import { useCallback, useState } from 'react'
import {
  addEntry,
  clearHistory,
  isExpiredByAge,
  readHistory,
  type HistoryEntry,
} from '../lib/history'

export interface LiveResult {
  /** Result blob, present only for a genuinely downloadable conversion. */
  blob?: Blob
  filename: string
  /** Source file, kept so Re-run can reconvert. Session-only, like the blob. */
  file?: File
}

// Session-scoped live payloads (result blob + source File), keyed by entry id.
// Module-level on purpose: navigating between routes unmounts the page hook, but
// the tab keeps this map, so results promised "while the tab is open" survive a
// trip to /about and back. A full reload clears it, which is the intended
// "expired" boundary. The metadata list itself rehydrates from localStorage.
const liveResults = new Map<string, LiveResult>()

// Drop live payloads for ids no longer in the capped list. Without this a
// long-lived tab pins every File/Blob ever processed; here it is bounded to the
// 20 visible rows.
function pruneLive(current: HistoryEntry[]): void {
  const keep = new Set(current.map((e) => e.id))
  for (const id of liveResults.keys()) {
    if (!keep.has(id)) liveResults.delete(id)
  }
}

export function useHistory() {
  const [entries, setEntries] = useState<HistoryEntry[]>(readHistory)

  const record = useCallback((entry: HistoryEntry, live?: LiveResult) => {
    const next = addEntry(entry)
    if (live) liveResults.set(entry.id, live)
    pruneLive(next)
    setEntries(next)
  }, [])

  // Downloadable only while its result blob is still in this session and the
  // entry has not aged past the 24h window.
  const isLive = useCallback(
    (entry: HistoryEntry) => !!liveResults.get(entry.id)?.blob && !isExpiredByAge(entry),
    [],
  )

  const getLive = useCallback((id: string) => liveResults.get(id), [])

  const clear = useCallback(() => {
    clearHistory()
    liveResults.clear()
    setEntries([])
  }, [])

  return { entries, record, isLive, getLive, clear }
}
