import { renderHook, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { _resetThemesCacheForTests, useThemes } from '../../src/hooks/useThemes'
import type { Theme } from '../../src/lib/api'

const THEMES: Theme[] = [
  { slug: 'default', name: 'Default', description: '', family: 'general' },
  { slug: 'academic', name: 'Academic', description: 'Serif.', family: 'serif' },
  { slug: 'business', name: 'Business', description: 'Accent.', family: 'sans' },
]

function okResponse(body: unknown): Response {
  return { ok: true, status: 200, json: async () => body } as Response
}

beforeEach(() => {
  _resetThemesCacheForTests()
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('useThemes', () => {
  it('fetches the theme list once across multiple hook instances', async () => {
    const fetchMock = vi.fn(async () => okResponse(THEMES))
    vi.stubGlobal('fetch', fetchMock)

    const first = renderHook(() => useThemes())
    await waitFor(() => expect(first.result.current.status).toBe('ready'))

    // A second instance reads the in-memory cache: no extra network call.
    const second = renderHook(() => useThemes())
    await waitFor(() => expect(second.result.current.status).toBe('ready'))

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(first.result.current.themes.map((t) => t.slug)).toEqual([
      'default',
      'academic',
      'business',
    ])
  })

  it('falls back to a single default tile when the API returns empty', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => okResponse([])))

    const { result } = renderHook(() => useThemes())
    await waitFor(() => expect(result.current.status).toBe('ready'))

    expect(result.current.themes).toHaveLength(1)
    expect(result.current.themes[0].slug).toBe('default')
  })

  it('surfaces an error and keeps the default tile when the fetch fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new Error('network down')
      }),
    )

    const { result } = renderHook(() => useThemes())
    await waitFor(() => expect(result.current.status).toBe('error'))

    expect(result.current.error).toBe('network down')
    expect(result.current.themes.map((t) => t.slug)).toEqual(['default'])
  })
})
