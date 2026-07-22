/* Local conversion history (#63).
 *
 * A browser-only list of recent conversions under `md-bridge:history`. The
 * project's no-persistence rule is about the SERVER; the browser is fair game.
 * Only lightweight metadata is stored (name, size, options, timestamp) - never
 * the File or the result blob. The result blob lives in memory for the tab's
 * session (see useHistory); once the tab reloads or 24h pass, the row is
 * "expired" and offers Re-run. Entries themselves are evicted only by the FIFO
 * cap, so an expired row stays visible and re-runnable. */

const HISTORY_KEY = 'md-bridge:history'
const MAX_ENTRIES = 20
export const HISTORY_TTL_MS = 24 * 60 * 60 * 1000

export type ConversionPair = 'pdf-to-md' | 'md-to-pdf'

export interface HistoryEntry {
  id: string
  /** Display name, e.g. "file.pdf" or "notes.md → PDF". */
  name: string
  pair: ConversionPair
  size: number
  /** pdf-to-md only: page count from the inspect pass. */
  pages?: number
  /** Enough to rebuild the call on Re-run. */
  options: { theme?: string }
  outcome: 'done' | 'needs_ocr'
  /** epoch ms. */
  createdAt: number
}

function safeParse(raw: string | null): HistoryEntry[] {
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? (parsed as HistoryEntry[]) : []
  } catch {
    return []
  }
}

/** Whether the result blob has aged out (24h), independent of the session. */
export function isExpiredByAge(entry: HistoryEntry, now: number = Date.now()): boolean {
  return now - entry.createdAt >= HISTORY_TTL_MS
}

/** Read the history, newest first. Defensive FIFO cap in case a stored blob
 *  grew past the cap. Entries are NOT dropped by age - only the FIFO cap evicts,
 *  so an aged (expired) row stays visible with a Re-run action. */
export function readHistory(): HistoryEntry[] {
  if (typeof window === 'undefined') return []
  return safeParse(window.localStorage.getItem(HISTORY_KEY)).slice(0, MAX_ENTRIES)
}

/** Prepend a new entry, enforce the FIFO cap, persist, and return the new list. */
export function addEntry(entry: HistoryEntry): HistoryEntry[] {
  const next = [entry, ...readHistory()].slice(0, MAX_ENTRIES)
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(HISTORY_KEY, JSON.stringify(next))
  }
  return next
}

/** Empty the history (the Clear all action). */
export function clearHistory(): void {
  if (typeof window !== 'undefined') window.localStorage.removeItem(HISTORY_KEY)
}
