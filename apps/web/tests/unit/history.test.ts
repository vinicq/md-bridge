import { beforeEach, afterEach, describe, expect, it } from 'vitest'
import {
  addEntry,
  clearHistory,
  readHistory,
  isExpiredByAge,
  HISTORY_TTL_MS,
  type HistoryEntry,
} from '../../src/lib/history'

const HISTORY_KEY = 'md-bridge:history'

function entry(over: Partial<HistoryEntry> = {}): HistoryEntry {
  return {
    id: over.id ?? `id-${Math.random().toString(36).slice(2)}`,
    name: 'file.pdf',
    pair: 'pdf-to-md',
    size: 1000,
    options: {},
    outcome: 'done',
    createdAt: 1_000_000,
    ...over,
  }
}

describe('history store (#63)', () => {
  beforeEach(() => window.localStorage.clear())
  afterEach(() => window.localStorage.clear())

  it('prepends newest first and round-trips every field', () => {
    addEntry(entry({ id: 'a', name: 'a.pdf', pages: 12, options: { theme: 'academic' } }))
    addEntry(entry({ id: 'b', name: 'b.pdf' }))
    const list = readHistory()
    expect(list.map((e) => e.id)).toEqual(['b', 'a'])
    expect(list[1]).toMatchObject({ name: 'a.pdf', pages: 12, options: { theme: 'academic' } })
  })

  it('enforces the FIFO cap of 20, evicting the oldest', () => {
    for (let i = 0; i < 25; i += 1) addEntry(entry({ id: `id-${i}` }))
    const list = readHistory()
    expect(list).toHaveLength(20)
    // newest (id-24) at the front, oldest kept is id-5 (0..4 evicted)
    expect(list[0].id).toBe('id-24')
    expect(list.at(-1)!.id).toBe('id-5')
  })

  it('detects age-based expiry at the 24h cutoff, keeping the entry', () => {
    const now = 100 * HISTORY_TTL_MS
    expect(isExpiredByAge(entry({ createdAt: now - HISTORY_TTL_MS - 1 }), now)).toBe(true)
    expect(isExpiredByAge(entry({ createdAt: now - 1000 }), now)).toBe(false)
    // an aged entry is still readable (only the FIFO cap evicts, not age).
    addEntry(entry({ id: 'old', createdAt: 1 }))
    expect(readHistory().some((e) => e.id === 'old')).toBe(true)
  })

  it('tolerates a corrupted blob and clears', () => {
    window.localStorage.setItem(HISTORY_KEY, '{not json')
    expect(readHistory()).toEqual([])
    addEntry(entry({ id: 'x' }))
    clearHistory()
    expect(readHistory()).toEqual([])
  })
})
