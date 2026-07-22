import { beforeEach, afterEach, describe, expect, it } from 'vitest'
import {
  addPreset,
  clearPresets,
  importPresets,
  parseImport,
  PRESET_CAP,
  readPresets,
  removePreset,
  serializePresets,
  type Preset,
} from '../../src/lib/presets'

const KEY = 'md-bridge:presets:md-to-pdf'

function preset(over: Partial<Preset> = {}): Preset {
  return {
    id: over.id ?? `id-${Math.random().toString(36).slice(2)}`,
    name: over.name ?? 'Briefs',
    pair: 'md-to-pdf',
    options: { theme: 'academic', custom_css: '' },
    createdAt: 1_000_000,
    ...over,
  }
}

describe('presets store (#62)', () => {
  beforeEach(() => window.localStorage.clear())
  afterEach(() => window.localStorage.clear())

  it('round-trips a preset scoped by format pair', () => {
    addPreset('md-to-pdf', preset({ id: 'a', name: 'A' }))
    expect(readPresets('md-to-pdf').map((p) => p.name)).toEqual(['A'])
    // A different pair has its own bucket.
    expect(readPresets('pdf-to-md')).toEqual([])
    expect(JSON.parse(window.localStorage.getItem(KEY)!)[0].name).toBe('A')
  })

  it('hard-rejects at the cap of 12 instead of evicting (named data)', () => {
    for (let i = 0; i < PRESET_CAP; i += 1) addPreset('md-to-pdf', preset({ id: `id-${i}`, name: `p${i}` }))
    expect(readPresets('md-to-pdf')).toHaveLength(12)
    // The 13th is refused; nothing is dropped.
    expect(addPreset('md-to-pdf', preset({ id: 'over', name: 'over' }))).toBeNull()
    expect(readPresets('md-to-pdf')).toHaveLength(12)
    expect(readPresets('md-to-pdf').some((p) => p.name === 'over')).toBe(false)
  })

  it('removes and clears', () => {
    addPreset('md-to-pdf', preset({ id: 'a', name: 'A' }))
    addPreset('md-to-pdf', preset({ id: 'b', name: 'B' }))
    expect(removePreset('md-to-pdf', 'a').map((p) => p.name)).toEqual(['B'])
    clearPresets('md-to-pdf')
    expect(readPresets('md-to-pdf')).toEqual([])
  })

  it('drops corrupt entries and tolerates a bad blob', () => {
    window.localStorage.setItem(KEY, '{not json')
    expect(readPresets('md-to-pdf')).toEqual([])
    window.localStorage.setItem(KEY, JSON.stringify([preset({ id: 'ok', name: 'ok' }), { junk: true }]))
    expect(readPresets('md-to-pdf').map((p) => p.name)).toEqual(['ok'])
  })

  it('parseImport rejects malformed JSON and payloads with no valid preset', () => {
    expect(parseImport('{not json')).toBeNull()
    expect(parseImport(JSON.stringify([{ nope: 1 }]))).toBeNull()
    expect(parseImport(JSON.stringify({ also: 'bad' }))).toBeNull()
    // A single object is accepted, not only arrays.
    const one = parseImport(JSON.stringify(preset({ id: 'x', name: 'X' })))
    expect(one?.map((p) => p.name)).toEqual(['X'])
  })

  it('imports with dedupe-by-name and cap accounting', () => {
    addPreset('md-to-pdf', preset({ id: 'a', name: 'A' }))
    // One new (B) and one same-name update (A).
    const r = importPresets('md-to-pdf', [preset({ id: 'a2', name: 'A' }), preset({ id: 'b', name: 'B' })])
    expect(r.imported).toBe(1) // only B is a new slot
    expect(r.ignored).toBe(0)
    expect(readPresets('md-to-pdf').map((p) => p.name).sort()).toEqual(['A', 'B'])
  })

  it('ignores imports that would exceed the cap', () => {
    for (let i = 0; i < PRESET_CAP; i += 1) addPreset('md-to-pdf', preset({ id: `id-${i}`, name: `p${i}` }))
    const r = importPresets('md-to-pdf', [preset({ id: 'x', name: 'brand-new' })])
    expect(r.imported).toBe(0)
    expect(r.ignored).toBe(1)
    expect(readPresets('md-to-pdf')).toHaveLength(12)
  })

  it('serializes the current pair as pretty JSON (the export payload)', () => {
    addPreset('md-to-pdf', preset({ id: 'a', name: 'A' }))
    const json = serializePresets('md-to-pdf')
    expect(JSON.parse(json)[0].name).toBe('A')
    expect(json).toContain('\n') // pretty-printed
  })
})
