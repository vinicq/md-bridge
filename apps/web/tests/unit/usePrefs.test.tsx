import { beforeEach, afterEach, describe, expect, it } from 'vitest'
import {
  applyPrefsToDocument,
  clearAllPrefs,
  readPrefs,
  writePrefs,
  DEFAULT_ACCENT,
} from '../../src/lib/prefs'

const PREFS_KEY = 'md-bridge:prefs'

describe('prefs store (#64)', () => {
  beforeEach(() => {
    window.localStorage.clear()
    document.documentElement.removeAttribute('data-reduce-motion')
    document.documentElement.style.removeProperty('--c-accent')
  })
  afterEach(() => {
    window.localStorage.clear()
    document.documentElement.removeAttribute('data-reduce-motion')
    document.documentElement.style.removeProperty('--c-accent')
  })

  it('round-trips a written patch through the unified key', () => {
    writePrefs({ accent: '#123456', pageSize: 'Letter' })
    const prefs = readPrefs()
    expect(prefs.accent).toBe('#123456')
    expect(prefs.pageSize).toBe('Letter')
    expect(JSON.parse(window.localStorage.getItem(PREFS_KEY)!).accent).toBe('#123456')
  })

  it('defaults fill fields absent from a partial stored blob (merge on read)', () => {
    // A blob written by an older release that only knew about `accent`.
    window.localStorage.setItem(PREFS_KEY, JSON.stringify({ accent: '#0000ff' }))
    const prefs = readPrefs()
    expect(prefs.accent).toBe('#0000ff')
    expect(prefs.pageSize).toBe('A4')
    expect(prefs.previewNewTab).toBe(false)
    expect(prefs.reduceMotion).toBeNull()
  })

  it('migrates the legacy MD-to-PDF theme key and leaves it in place', () => {
    window.localStorage.setItem('md-bridge:md-to-pdf:theme', 'academic')

    const prefs = readPrefs()
    expect(prefs.defaultPdfTheme).toBe('academic')

    // consolidated into the unified key...
    const unified = JSON.parse(window.localStorage.getItem(PREFS_KEY)!)
    expect(unified.defaultPdfTheme).toBe('academic')
    // ...and the legacy key survives for one release (backwards compat).
    expect(window.localStorage.getItem('md-bridge:md-to-pdf:theme')).toBe('academic')
  })

  it('clearAllPrefs removes every md-bridge:* key and nothing else', () => {
    window.localStorage.setItem('md-bridge:prefs', '{}')
    window.localStorage.setItem('md-bridge:history', '[]')
    window.localStorage.setItem('md-bridge:locale', 'pt')
    window.localStorage.setItem('unrelated:key', 'keep')

    clearAllPrefs()

    expect(window.localStorage.getItem('md-bridge:prefs')).toBeNull()
    expect(window.localStorage.getItem('md-bridge:history')).toBeNull()
    expect(window.localStorage.getItem('md-bridge:locale')).toBeNull()
    expect(window.localStorage.getItem('unrelated:key')).toBe('keep')
  })

  it('applyPrefsToDocument writes the accent variable and reduce-motion flag', () => {
    const root = document.documentElement
    applyPrefsToDocument({
      defaultPdfTheme: 'default',
      pageSize: 'A4',
      previewNewTab: false,
      accent: '#abcdef',
      reduceMotion: true,
    })
    expect(root.style.getPropertyValue('--c-accent')).toBe('#abcdef')
    expect(root.getAttribute('data-reduce-motion')).toBe('true')
  })

  it('applyPrefsToDocument removes the reduce-motion flag when following the OS', () => {
    const root = document.documentElement
    root.setAttribute('data-reduce-motion', 'true')
    applyPrefsToDocument({
      defaultPdfTheme: 'default',
      pageSize: 'A4',
      previewNewTab: false,
      accent: DEFAULT_ACCENT,
      reduceMotion: null,
    })
    expect(root.hasAttribute('data-reduce-motion')).toBe(false)
  })
})
