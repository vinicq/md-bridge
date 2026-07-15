import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useBatchConvert } from '../../src/hooks/useBatchConvert'

interface Res {
  md: string
}

/**
 * Flush enough microtasks for the loop to enter the first item's `converting`
 * state. `waitFor` is avoided because it polls on timers, which are faked here.
 */
async function settle() {
  await act(async () => {
    await Promise.resolve()
    await Promise.resolve()
    await Promise.resolve()
  })
}

function pdf(name: string): File {
  return new File(['%PDF-1.4'], name, { type: 'application/pdf' })
}

/**
 * Convert mock: a file marked `resolve` completes immediately; anything else
 * hangs until its signal aborts and then rejects, the way a real `fetch`
 * rejects with an AbortError when the request is cancelled.
 */
function makeConvert(behavior: Record<string, 'resolve'>) {
  return vi.fn((file: File, signal: AbortSignal): Promise<Res> => {
    if (behavior[file.name] === 'resolve') return Promise.resolve({ md: `# ${file.name}` })
    return new Promise<Res>((_resolve, reject) => {
      signal.addEventListener('abort', () =>
        reject(new DOMException('Aborted', 'AbortError')),
      )
    })
  })
}

describe('useBatchConvert', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('times out a stuck item and still runs the next one', async () => {
    const convert = makeConvert({ 'ok.pdf': 'resolve' })
    const { result } = renderHook(() =>
      useBatchConvert<Res>({ convert, convertTimeoutMs: 1000 }),
    )

    act(() => result.current.add([pdf('stuck.pdf'), pdf('ok.pdf')]))

    let run!: Promise<void>
    act(() => {
      run = result.current.runAll()
    })

    // The ceiling fires for the stuck item; the loop must move on to ok.pdf.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000)
      await run
    })

    expect(result.current.items[0].status).toBe('error')
    expect(result.current.items[0].error?.code).toBe('timeout')
    // The regression guard: the second item is not stranded behind the first.
    expect(result.current.items[1].status).toBe('done')
    expect(result.current.running).toBe(false)
  })

  it('skips a single in-flight item without blocking the batch', async () => {
    const convert = makeConvert({ 'ok.pdf': 'resolve' })
    const { result } = renderHook(() => useBatchConvert<Res>({ convert }))

    act(() => result.current.add([pdf('stuck.pdf'), pdf('ok.pdf')]))

    let run!: Promise<void>
    act(() => {
      run = result.current.runAll()
    })

    // Let the first item enter `converting`, then skip it by id.
    await settle()
    expect(result.current.items[0].status).toBe('converting')
    const stuckId = result.current.items[0].id
    await act(async () => {
      result.current.skip(stuckId)
      await run
    })

    expect(result.current.items[0].status).toBe('error')
    expect(result.current.items[0].error?.code).toBe('skipped')
    expect(result.current.items[1].status).toBe('done')
    expect(result.current.running).toBe(false)
  })

  it('without a ceiling, an item is never timed out', async () => {
    const convert = makeConvert({})
    const { result } = renderHook(() => useBatchConvert<Res>({ convert }))

    act(() => result.current.add([pdf('stuck.pdf')]))
    act(() => {
      void result.current.runAll()
    })

    await settle()
    expect(result.current.items[0].status).toBe('converting')
    await act(async () => {
      await vi.advanceTimersByTimeAsync(60 * 60 * 1000)
    })

    // Still converting after an hour: default behavior is preserved.
    expect(result.current.items[0].status).toBe('converting')
  })

  it('clear aborts the run and empties the queue', async () => {
    const convert = makeConvert({})
    const { result } = renderHook(() => useBatchConvert<Res>({ convert }))

    act(() => result.current.add([pdf('stuck.pdf'), pdf('ok.pdf')]))
    act(() => {
      void result.current.runAll()
    })
    await settle()
    expect(result.current.items[0].status).toBe('converting')

    act(() => result.current.clear())

    expect(result.current.items).toHaveLength(0)
    expect(result.current.running).toBe(false)
  })

  it('converts when the queue is rebuilt and run in one act (clear -> add -> runAll)', async () => {
    // Regression guard for the /md-to-pdf theme re-run: the page clears the
    // queue, re-adds the same files, and calls runAll() in a single tick. When
    // runAll snapshotted the queue through a setState updater, it read the empty
    // post-clear state and converted nothing. runAll now reads a synchronous
    // itemsRef, so the freshly-added item is seen and converted.
    const convert = makeConvert({ 'a.pdf': 'resolve' })
    const { result } = renderHook(() => useBatchConvert<Res>({ convert }))

    act(() => result.current.add([pdf('a.pdf')]))

    let run!: Promise<void>
    act(() => {
      result.current.clear()
      result.current.add([pdf('a.pdf')])
      run = result.current.runAll()
    })
    await act(async () => {
      await run
    })

    expect(convert).toHaveBeenCalledTimes(1)
    expect(result.current.items).toHaveLength(1)
    expect(result.current.items[0].status).toBe('done')
    expect(result.current.running).toBe(false)
  })

  it('does not convert a queued item removed mid-run (#357)', async () => {
    // gate.pdf hangs so the run is in flight; remove-me.pdf is still queued when
    // we drop it; after.pdf follows so the loop keeps going past the hole. We
    // skip gate.pdf to advance, and the loop must reach after.pdf without ever
    // converting the removed remove-me.pdf.
    const convert = makeConvert({ 'remove-me.pdf': 'resolve', 'after.pdf': 'resolve' })
    const { result } = renderHook(() => useBatchConvert<Res>({ convert }))

    act(() => result.current.add([pdf('gate.pdf'), pdf('remove-me.pdf'), pdf('after.pdf')]))
    let run!: Promise<unknown>
    act(() => {
      run = result.current.runAll()
    })
    await settle()
    expect(result.current.items[0].status).toBe('converting')

    const gateId = result.current.items[0].id
    const removeId = result.current.items[1].id
    await act(async () => {
      result.current.remove(removeId) // drop the queued item mid-run
      result.current.skip(gateId) // release the gate so the loop advances
      await run
    })

    const converted = convert.mock.calls.map((c) => (c[0] as File).name)
    // The loop reached after.pdf (proving it advanced past the hole) but never
    // touched the removed item.
    expect(converted).toContain('after.pdf')
    expect(converted).not.toContain('remove-me.pdf')
  })

  it('aborts the in-flight request when a converting item is removed (#357)', async () => {
    const convert = makeConvert({})
    const { result } = renderHook(() => useBatchConvert<Res>({ convert }))

    act(() => result.current.add([pdf('stuck.pdf')]))
    act(() => {
      void result.current.runAll()
    })
    await settle()
    expect(result.current.items[0].status).toBe('converting')

    // The signal handed to convert() must abort when the item is removed.
    const signal = convert.mock.calls[0][1] as AbortSignal
    expect(signal.aborted).toBe(false)
    const convertingId = result.current.items[0].id
    act(() => result.current.remove(convertingId))
    expect(signal.aborted).toBe(true)
  })

  it('reorders queued items by direction and drop target', () => {
    const convert = makeConvert({})
    const { result } = renderHook(() => useBatchConvert<Res>({ convert }))

    act(() => result.current.add([pdf('a.pdf'), pdf('b.pdf'), pdf('c.pdf')]))
    const [a, b, c] = result.current.items

    act(() => result.current.move(c.id, -1))
    expect(result.current.items.map((it) => it.file.name)).toEqual(['a.pdf', 'c.pdf', 'b.pdf'])

    act(() => result.current.moveTo(a.id, b.id))
    expect(result.current.items.map((it) => it.file.name)).toEqual(['c.pdf', 'b.pdf', 'a.pdf'])
  })

  it('does not reorder while the batch is running', async () => {
    const convert = makeConvert({})
    const { result } = renderHook(() => useBatchConvert<Res>({ convert }))

    act(() => result.current.add([pdf('a.pdf'), pdf('b.pdf')]))
    act(() => {
      void result.current.runAll()
    })
    await settle()

    const [a, b] = result.current.items
    act(() => {
      result.current.move(b.id, -1)
      result.current.moveTo(b.id, a.id)
    })

    expect(result.current.items.map((it) => it.file.name)).toEqual(['a.pdf', 'b.pdf'])
  })
})
