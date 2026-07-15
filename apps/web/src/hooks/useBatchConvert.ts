import { useCallback, useEffect, useRef, useState } from 'react'

export type BatchStatus = 'queued' | 'converting' | 'done' | 'error'

/** Outcome of a single runAll() pass, read from the real post-run state so the
 *  caller can pick a toast that matches what happened (#353). */
export interface BatchRunSummary {
  /** Items this run actually processed (queued at snapshot time, still present). */
  processed: number
  done: number
  failed: number
}

export interface BatchItem<TResult> {
  id: string
  file: File
  status: BatchStatus
  result: TResult | null
  error: { code: string; message: string } | null
  /** Object URL for results that exposed as a blob (used by the MD to PDF flow). */
  blobUrl: string | null
}

interface UseBatchConvertOptions<TResult> {
  convert: (file: File, signal: AbortSignal) => Promise<TResult>
  /** Optionally turn the result into an object URL the UI can preview or download. */
  toBlobUrl?: (result: TResult) => string | null
  /**
   * Per-item ceiling in milliseconds. When set, an item that stays in flight
   * longer than this is aborted, marked `error` with code `timeout`, and the
   * loop moves on. Default `undefined` keeps the previous behavior (no ceiling),
   * so the feature is opt-in and a plain revert removes it.
   */
  convertTimeoutMs?: number
}

function makeId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
}

export function useBatchConvert<TResult>({
  convert,
  toBlobUrl,
  convertTimeoutMs,
}: UseBatchConvertOptions<TResult>) {
  const [items, setItemsState] = useState<BatchItem<TResult>[]>([])
  // Mirror of `items` kept in sync on every write. runAll() reads it directly
  // instead of snapshotting through a setState updater: when the queue is
  // rebuilt and run in the same tick (clear -> add -> runAll, e.g. the theme
  // re-run on /md-to-pdf), a setState snapshot can still observe the empty
  // post-clear state and convert nothing. A ref reflects each write at once.
  const itemsRef = useRef<BatchItem<TResult>[]>([])
  const setItems = useCallback(
    (updater: BatchItem<TResult>[] | ((prev: BatchItem<TResult>[]) => BatchItem<TResult>[])) => {
      const next = typeof updater === 'function' ? updater(itemsRef.current) : updater
      itemsRef.current = next
      setItemsState(next)
    },
    [],
  )
  const [running, setRunning] = useState(false)
  const abortRef = useRef<AbortController | null>(null)
  // One controller per in-flight item, so the user can skip a single stuck
  // item without aborting the whole batch.
  const itemCtrlsRef = useRef<Map<string, AbortController>>(new Map())
  const blobUrlsRef = useRef<string[]>([])

  useEffect(() => {
    return () => {
      for (const url of blobUrlsRef.current) URL.revokeObjectURL(url)
    }
  }, [])

  const patch = useCallback((id: string, patch: Partial<BatchItem<TResult>>) => {
    setItems((prev) => prev.map((it) => (it.id === id ? { ...it, ...patch } : it)))
  }, [])

  const add = useCallback((files: File[]) => {
    if (files.length === 0) return
    setItems((prev) => [
      ...prev,
      ...files.map<BatchItem<TResult>>((file) => ({
        id: makeId(),
        file,
        status: 'queued',
        result: null,
        error: null,
        blobUrl: null,
      })),
    ])
  }, [])

  const remove = useCallback((id: string) => {
    setItems((prev) => {
      const target = prev.find((it) => it.id === id)
      if (target?.blobUrl) {
        URL.revokeObjectURL(target.blobUrl)
        blobUrlsRef.current = blobUrlsRef.current.filter((u) => u !== target.blobUrl)
      }
      return prev.filter((it) => it.id !== id)
    })
  }, [])

  const move = useCallback((id: string, direction: -1 | 1) => {
    if (running) return
    setItems((prev) => {
      const from = prev.findIndex((it) => it.id === id)
      if (from === -1) return prev
      const to = from + direction
      if (to < 0 || to >= prev.length) return prev
      const next = [...prev]
      const [item] = next.splice(from, 1)
      next.splice(to, 0, item)
      return next
    })
  }, [running])

  const moveTo = useCallback((id: string, targetId: string) => {
    if (running) return
    if (id === targetId) return
    setItems((prev) => {
      const from = prev.findIndex((it) => it.id === id)
      const target = prev.findIndex((it) => it.id === targetId)
      if (from === -1 || target === -1) return prev
      const next = [...prev]
      const [item] = next.splice(from, 1)
      next.splice(target, 0, item)
      return next
    })
  }, [running])

  const clear = useCallback(() => {
    abortRef.current?.abort()
    itemCtrlsRef.current.clear()
    for (const url of blobUrlsRef.current) URL.revokeObjectURL(url)
    blobUrlsRef.current = []
    setItems([])
    setRunning(false)
  }, [])

  // Abort a single in-flight item without touching the rest of the batch. The
  // loop classifies this abort as `skipped` and proceeds to the next item.
  const skip = useCallback((id: string) => {
    itemCtrlsRef.current.get(id)?.abort()
  }, [])

  // Snapshot the current queue and process each `queued` item in order. New
  // items added while the run is in flight stay queued until the next call.
  const runAll = useCallback(async (): Promise<BatchRunSummary> => {
    if (running) return { processed: 0, done: 0, failed: 0 }
    const ctrl = new AbortController()
    abortRef.current = ctrl
    setRunning(true)

    // Capture the IDs to process so we don't re-run items the user might add
    // mid-flight (they remain queued, ready for the next click). itemsRef is
    // current as of the last write, so no setState flush wait is needed.
    const snapshot = itemsRef.current
    const targets = snapshot.filter((it) => it.status === 'queued').map((it) => it.id)

    for (const id of targets) {
      if (ctrl.signal.aborted) break
      const file = snapshot.find((it) => it.id === id)?.file
      if (!file) continue
      patch(id, { status: 'converting' })

      // Each item gets its own controller (for skip) and an optional timeout
      // controller. The effective signal aborts if the batch is cleared, the
      // item is skipped, or the ceiling is reached. We discriminate the three
      // sources by checking each controller, never the combined signal: the
      // combined signal is aborted for all three, so reading it would turn a
      // skip or timeout into a full-batch break.
      const itemCtrl = new AbortController()
      itemCtrlsRef.current.set(id, itemCtrl)
      const timeoutCtrl = convertTimeoutMs ? new AbortController() : null
      const timeoutId = timeoutCtrl
        ? setTimeout(() => timeoutCtrl.abort(), convertTimeoutMs)
        : undefined
      const signals = [ctrl.signal, itemCtrl.signal]
      if (timeoutCtrl) signals.push(timeoutCtrl.signal)
      const signal = AbortSignal.any(signals)

      try {
        const result = await convert(file, signal)
        if (ctrl.signal.aborted) break
        const blobUrl = toBlobUrl ? toBlobUrl(result) : null
        if (blobUrl) blobUrlsRef.current.push(blobUrl)
        patch(id, { status: 'done', result, blobUrl, error: null })
      } catch (err) {
        if (ctrl.signal.aborted) break
        if (timeoutCtrl?.signal.aborted) {
          // Message stays empty: BatchPanel maps the code to a localized
          // string so i18n lives in the component, not the hook.
          patch(id, { status: 'error', error: { code: 'timeout', message: '' } })
          continue
        }
        if (itemCtrl.signal.aborted) {
          patch(id, { status: 'error', error: { code: 'skipped', message: '' } })
          continue
        }
        const message =
          err && typeof err === 'object' && 'message' in err
            ? String((err as Error).message)
            : 'Unknown error'
        const code =
          err && typeof err === 'object' && 'code' in err
            ? String((err as { code: unknown }).code)
            : 'unknown'
        patch(id, { status: 'error', error: { code, message } })
      } finally {
        if (timeoutId !== undefined) clearTimeout(timeoutId)
        itemCtrlsRef.current.delete(id)
      }
    }

    setRunning(false)

    // Read the outcome from the live ref, not the stale `items` closure the
    // caller captured before awaiting: only items still present are counted, so
    // a mid-run remove drops out of the summary too (#353, #357).
    const targetSet = new Set(targets)
    const processed = itemsRef.current.filter((it) => targetSet.has(it.id))
    return {
      processed: processed.length,
      done: processed.filter((it) => it.status === 'done').length,
      failed: processed.filter((it) => it.status === 'error').length,
    }
  }, [convert, convertTimeoutMs, patch, running, toBlobUrl])

  return { items, running, add, remove, move, moveTo, clear, skip, runAll }
}
