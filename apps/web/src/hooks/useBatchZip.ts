import { useCallback } from 'react'
import { createStoreZip, type ZipEntry } from '../lib/zipStore'
import type { BatchItem } from './useBatchConvert'

interface UseBatchZipOptions<TResult> {
  /** Turn a done item into a zip entry (name + bytes). May be async because a
   *  result can be a Blob whose bytes are read with arrayBuffer(). */
  toEntry: (item: BatchItem<TResult>) => Promise<ZipEntry> | ZipEntry
}

/** Insert a counter before the file extension so repeated names stay unique
 *  inside the archive: "report.md" -> "report (2).md". */
function uniqueName(name: string, n: number): string {
  if (n === 0) return name
  const dot = name.lastIndexOf('.')
  if (dot <= 0) return `${name} (${n + 1})`
  return `${name.slice(0, dot)} (${n + 1})${name.slice(dot)}`
}

/**
 * Generic client-side "download all" helper: collects the done items, turns each
 * into a zip entry, and triggers a single archive download. The zip is built by
 * the dependency-free store-only encoder, so the bytes are deterministic.
 */
export function useBatchZip<TResult>({ toEntry }: UseBatchZipOptions<TResult>) {
  const downloadZip = useCallback(
    async (items: BatchItem<TResult>[], bundleName: string) => {
      const done = items.filter((it) => it.status === 'done' && it.result != null)
      if (done.length === 0) return

      const raw = await Promise.all(done.map((it) => toEntry(it)))
      const seen = new Map<string, number>()
      const entries: ZipEntry[] = raw.map((e) => {
        const n = seen.get(e.name) ?? 0
        seen.set(e.name, n + 1)
        return { name: uniqueName(e.name, n), data: e.data }
      })

      const blob = new Blob([createStoreZip(entries)], { type: 'application/zip' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = bundleName
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    },
    [toEntry],
  )

  return { downloadZip }
}
