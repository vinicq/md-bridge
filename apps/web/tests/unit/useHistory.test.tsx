import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { useHistory } from '../../src/hooks/useHistory'
import type { HistoryEntry } from '../../src/lib/history'

function entry(over: Partial<HistoryEntry> = {}): HistoryEntry {
  return {
    id: over.id ?? `id-${Math.random().toString(36).slice(2)}`,
    name: 'file.pdf',
    pair: 'pdf-to-md',
    size: 1000,
    options: {},
    outcome: 'done',
    createdAt: Date.now(),
    ...over,
  }
}

function blobResult(): { blob: Blob; filename: string; file: File } {
  return {
    blob: new Blob(['# hi'], { type: 'text/markdown' }),
    filename: 'file.md',
    file: new File(['x'], 'file.pdf', { type: 'application/pdf' }),
  }
}

describe('useHistory (#63)', () => {
  // clear() empties both localStorage and the module-scoped live registry, so it
  // is the isolation reset between tests.
  beforeEach(() => {
    const { result, unmount } = renderHook(() => useHistory())
    act(() => result.current.clear())
    unmount()
  })
  afterEach(() => window.localStorage.clear())

  it('records a live result and marks it live and downloadable', () => {
    const { result } = renderHook(() => useHistory())
    const e = entry({ id: 'a' })
    act(() => result.current.record(e, blobResult()))
    expect(result.current.getLive('a')?.file).toBeInstanceOf(File)
    expect(result.current.isLive(e)).toBe(true)
  })

  it('keeps live payloads across a route unmount (module-scoped registry)', () => {
    const first = renderHook(() => useHistory())
    act(() => first.result.current.record(entry({ id: 'keep' }), blobResult()))
    first.unmount() // navigate away: the page hook unmounts

    // Returning to the page mounts a fresh hook; the live blob must still be there.
    const second = renderHook(() => useHistory())
    expect(second.result.current.getLive('keep')?.blob).toBeInstanceOf(Blob)
  })

  it('prunes live payloads for entries evicted past the FIFO cap', () => {
    const { result } = renderHook(() => useHistory())
    act(() => {
      for (let i = 0; i < 21; i += 1) {
        result.current.record(entry({ id: `id-${i}` }), blobResult())
      }
    })
    // id-0 fell out of the 20-cap, so its live payload is dropped too.
    expect(result.current.getLive('id-0')).toBeUndefined()
    expect(result.current.getLive('id-20')?.blob).toBeInstanceOf(Blob)
  })

  it('is not downloadable without a blob (ocr_required keeps only the source file)', () => {
    const { result } = renderHook(() => useHistory())
    const e = entry({ id: 'ocr', outcome: 'needs_ocr' })
    const src = new File(['x'], 'scan.pdf', { type: 'application/pdf' })
    act(() => result.current.record(e, { filename: 'scan.md', file: src }))
    // No blob -> not live/downloadable, but the source file is retained for Re-run.
    expect(result.current.isLive(e)).toBe(false)
    expect(result.current.getLive('ocr')?.file).toBe(src)
  })
})
