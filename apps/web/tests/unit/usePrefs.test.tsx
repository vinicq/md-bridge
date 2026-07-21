import { beforeEach, afterEach, describe, expect, it } from 'vitest'
import { applyPrefsToDocument, clearAllPrefs, readPrefs, writePrefs } from '../../src/lib/prefs'

const PREFS_KEY = 'md-bridge:prefs'

describe('prefs store (#64)', () => {
  beforeEach(() => {
    window.localStorage.clear()
    document.documentElement.removeAttribute('data-reduce-motion')
  })
  afterEach(() => {
    window.localStorage.clear()
    document.documentElement.removeAttribute('data-reduce-motion')
  })

  it('round-trips a written patch through the unified key', () => {
    writePrefs({ defaultPdfTheme: 'academic', reduceMotion: true })
    const prefs = readPrefs()
    expect(prefs.defaultPdfTheme).toBe('academic')
    expect(prefs.reduceMotion).toBe(true)
    expect(JSON.parse(window.localStorage.getItem(PREFS_KEY)!).defaultPdfTheme).toBe('academic')
  })

  it('defaults fill fields absent from a partial stored blob (merge on read)', () => {
    // A blob written by an older release that only knew about defaultPdfTheme.
    window.localStorage.setItem(PREFS_KEY, JSON.stringify({ defaultPdfTheme: 'academic' }))
    const prefs = readPrefs()
    expect(prefs.defaultPdfTheme).toBe('academic')
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

  it('applyPrefsToDocument sets the reduce-motion flag only when forced true', () => {
    const root = document.documentElement
    applyPrefsToDocument({ defaultPdfTheme: 'default', reduceMotion: true })
    expect(root.getAttribute('data-reduce-motion')).toBe('true')
  })

  it('applyPrefsToDocument removes the reduce-motion flag when following the OS', () => {
    const root = document.documentElement
    root.setAttribute('data-reduce-motion', 'true')
    applyPrefsToDocument({ defaultPdfTheme: 'default', reduceMotion: null })
    expect(root.hasAttribute('data-reduce-motion')).toBe(false)
  })
})
