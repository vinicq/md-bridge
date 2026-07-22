/* React binding over the history store (#63). The persisted list holds only
 * metadata; the result blobs live in a session-scoped ref (empty after a
 * reload), so a row is "live" only while its blob is in this tab and within the
 * 24h window. */
import { useCallback, useRef, useState } from 'react'
import {
  addEntry,
  clearHistory,
  isExpiredByAge,
  readHistory,
  type HistoryEntry,
} from '../lib/history'

export interface LiveResult {
  blob: Blob
  filename: string
  /** Source file, kept so Re-run can reconvert. Session-only, like the blob. */
  file?: File
}

export function useHistory() {
  const [entries, setEntries] = useState<HistoryEntry[]>(readHistory)
  const liveRef = useRef<Map<string, LiveResult>>(new Map())

  const record = useCallback((entry: HistoryEntry, live?: LiveResult) => {
    setEntries(addEntry(entry))
    if (live) liveRef.current.set(entry.id, live)
  }, [])

  // A result is downloadable only while its blob is still in this session and
  // has not aged past the 24h window.
  const isLive = useCallback(
    (entry: HistoryEntry) => liveRef.current.has(entry.id) && !isExpiredByAge(entry),
    [],
  )

  const getLive = useCallback((id: string) => liveRef.current.get(id), [])

  const clear = useCallback(() => {
    clearHistory()
    liveRef.current.clear()
    setEntries([])
  }, [])

  return { entries, record, isLive, getLive, clear }
}
