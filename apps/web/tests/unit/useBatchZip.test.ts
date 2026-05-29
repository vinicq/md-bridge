import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useBatchZip } from '../../src/hooks/useBatchZip'
import type { BatchItem } from '../../src/hooks/useBatchConvert'

function item(id: string, name: string, status: BatchItem<string>['status'], result: string | null): BatchItem<string> {
  return { id, file: new File([''], name), status, result, error: null, blobUrl: null }
}

const enc = new TextEncoder()

describe('useBatchZip', () => {
  let clickSpy: ReturnType<typeof vi.spyOn>
  let lastDownloadName = ''

  beforeEach(() => {
    Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: vi.fn(() => 'blob:zip') })
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: vi.fn() })
    clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
      lastDownloadName = this.download
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
    lastDownloadName = ''
  })

  it('builds a zip from done items and downloads it under the bundle name', async () => {
    const { result } = renderHook(() =>
      useBatchZip<string>({ toEntry: (it) => ({ name: it.file.name, data: enc.encode(it.result ?? '') }) }),
    )
    const items = [
      item('1', 'a.md', 'done', '# a'),
      item('2', 'b.md', 'queued', null),
      item('3', 'c.md', 'done', '# c'),
    ]
    await act(async () => {
      await result.current.downloadZip(items, 'markdown.zip')
    })
    expect(URL.createObjectURL).toHaveBeenCalledTimes(1)
    expect(clickSpy).toHaveBeenCalledTimes(1)
    expect(lastDownloadName).toBe('markdown.zip')
  })

  it('does nothing when there is no done item', async () => {
    const { result } = renderHook(() =>
      useBatchZip<string>({ toEntry: (it) => ({ name: it.file.name, data: enc.encode(it.result ?? '') }) }),
    )
    await act(async () => {
      await result.current.downloadZip([item('1', 'a.md', 'queued', null)], 'markdown.zip')
    })
    expect(URL.createObjectURL).not.toHaveBeenCalled()
    expect(clickSpy).not.toHaveBeenCalled()
  })
})
