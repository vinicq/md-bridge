/* Single-key store for the settings that had no home of their own (#64).
 *
 * locale and theme already persist through their own providers
 * (`md-bridge:locale`, `md-bridge:theme`) and are edited through those
 * contexts; unifying those two into this key is a follow-up. Everything the
 * preferences page introduces (plus the MD→PDF default theme) lives here under
 * one `md-bridge:prefs` key, merged over the defaults on read so a field added
 * in a later release never breaks an older stored blob.
 *
 * The first read migrates the legacy `md-bridge:md-to-pdf:theme` key into the
 * unified key and leaves the original in place for one release (backwards
 * compat); a future release removes it. */

const PREFS_KEY = 'md-bridge:prefs'
const LEGACY_PDF_THEME_KEY = 'md-bridge:md-to-pdf:theme'

export type PageSize = 'A4' | 'Letter' | 'Legal'
export const PAGE_SIZES: readonly PageSize[] = ['A4', 'Letter', 'Legal']

export const DEFAULT_ACCENT = '#c8362f'

export interface Prefs {
  defaultPdfTheme: string
  pageSize: PageSize
  previewNewTab: boolean
  accent: string
  /** null follows the OS `prefers-reduced-motion`; true/false is a manual override. */
  reduceMotion: boolean | null
}

export const DEFAULTS: Prefs = {
  defaultPdfTheme: 'default',
  pageSize: 'A4',
  previewNewTab: false,
  accent: DEFAULT_ACCENT,
  reduceMotion: null,
}

function safeParse(raw: string | null): Partial<Prefs> | null {
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? (parsed as Partial<Prefs>) : null
  } catch {
    return null
  }
}

/**
 * Read the merged preferences. On the first read (no unified key yet) it
 * migrates the legacy MD→PDF theme key, persists the unified blob, and leaves
 * the legacy key untouched.
 */
export function readPrefs(): Prefs {
  if (typeof window === 'undefined') return { ...DEFAULTS }
  const stored = safeParse(window.localStorage.getItem(PREFS_KEY))
  if (stored) return { ...DEFAULTS, ...stored }
  const legacyPdfTheme = window.localStorage.getItem(LEGACY_PDF_THEME_KEY)
  const migrated: Prefs = {
    ...DEFAULTS,
    ...(legacyPdfTheme ? { defaultPdfTheme: legacyPdfTheme } : {}),
  }
  window.localStorage.setItem(PREFS_KEY, JSON.stringify(migrated))
  return migrated
}

/** Merge a patch into the stored preferences and persist. Returns the result. */
export function writePrefs(patch: Partial<Prefs>): Prefs {
  const next = { ...readPrefs(), ...patch }
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(PREFS_KEY, JSON.stringify(next))
  }
  return next
}

/** Clear every `md-bridge:*` key (the Reset all action). */
export function clearAllPrefs(): void {
  if (typeof window === 'undefined') return
  const ls = window.localStorage
  const doomed: string[] = []
  for (let i = 0; i < ls.length; i += 1) {
    const key = ls.key(i)
    if (key && key.startsWith('md-bridge:')) doomed.push(key)
  }
  doomed.forEach((key) => ls.removeItem(key))
}

/** Apply the document-level effects: accent CSS variable and reduce-motion flag. */
export function applyPrefsToDocument(prefs: Prefs): void {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  root.style.setProperty('--c-accent', prefs.accent)
  // Only `true` forces reduction; null (follow OS) and false (force motion, not
  // wired to the UI yet) both leave the OS `@media` rule as the sole authority.
  if (prefs.reduceMotion === true) {
    root.setAttribute('data-reduce-motion', 'true')
  } else {
    root.removeAttribute('data-reduce-motion')
  }
}
