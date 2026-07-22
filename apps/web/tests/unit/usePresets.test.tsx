import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { usePresets } from '../../src/hooks/usePresets'
import type { ImportResult, Preset } from '../../src/lib/presets'

function preset(over: Partial<Preset> = {}): Preset {
  return {
    id: over.id ?? `id-${Math.random().toString(36).slice(2)}`,
    name: over.name ?? 'P',
    pair: 'md-to-pdf',
    options: { theme: 'default' },
    createdAt: 1,
    ...over,
  }
}

describe('usePresets (#62)', () => {
  beforeEach(() => window.localStorage.clear())
  afterEach(() => window.localStorage.clear())

  it('saves and flips atCap after 12, then refuses the 13th', () => {
    const { result } = renderHook(() => usePresets('md-to-pdf'))
    act(() => {
      for (let i = 0; i < 12; i += 1) result.current.save(preset({ id: `id-${i}`, name: `p${i}` }))
    })
    expect(result.current.presets).toHaveLength(12)
    expect(result.current.atCap).toBe(true)

    let accepted = true
    act(() => {
      accepted = result.current.save(preset({ id: 'over', name: 'over' }))
    })
    expect(accepted).toBe(false)
    expect(result.current.presets).toHaveLength(12)
  })

  it('removes a preset', () => {
    const { result } = renderHook(() => usePresets('md-to-pdf'))
    act(() => {
      result.current.save(preset({ id: 'a', name: 'A' }))
    })
    act(() => result.current.remove('a'))
    expect(result.current.presets).toEqual([])
  })

  it('imports and returns the merge result', () => {
    const { result } = renderHook(() => usePresets('md-to-pdf'))
    let res: ImportResult | undefined
    act(() => {
      res = result.current.importFrom([preset({ id: 'x', name: 'X' })])
    })
    expect(res?.imported).toBe(1)
    expect(result.current.presets.map((p) => p.name)).toEqual(['X'])
  })
})
