/** Pure helpers for the Language Workshop page (#61). Kept out of the
 *  component so the completion math, the export serializers, and the draft
 *  persistence are unit-testable in isolation. */
import type { Locale } from './dictionaries'

export type FlatDict = Record<string, string>

/** Flatten a dictionary to dotted-path keys, keeping only string leaves.
 *  Function and array values (counted plurals, list copy) are not plain-text
 *  translatable, so they are excluded from the editable set. */
export function flattenDictionary(dict: unknown, prefix = ''): FlatDict {
  const out: FlatDict = {}
  if (dict == null || typeof dict !== 'object' || Array.isArray(dict)) return out
  for (const [key, value] of Object.entries(dict as Record<string, unknown>)) {
    const path = prefix ? `${prefix}.${key}` : key
    if (typeof value === 'string') {
      out[path] = value
    } else if (value && typeof value === 'object' && !Array.isArray(value)) {
      Object.assign(out, flattenDictionary(value, path))
    }
    // functions and arrays are intentionally skipped
  }
  return out
}

export interface Completion {
  total: number
  translated: number
  untranslated: string[]
  pct: number
}

/** Localization progress of a target locale against the English reference.
 *
 *  Every locale is type-complete (the Dictionary interface forces all keys),
 *  so "has a value" is always true and is useless as a signal. Instead a key
 *  counts as TRANSLATED when its effective value (the session draft if present,
 *  else the locale's current value) is non-empty AND differs from the English
 *  reference. A value still identical to English reads as untranslated. This is
 *  a proxy: a legitimately identical string (a brand name, "Markdown") shows as
 *  untranslated, which the page states up front. */
export function computeCompletion(
  enFlat: FlatDict,
  targetFlat: FlatDict,
  draft: Record<string, string> = {},
): Completion {
  const keys = Object.keys(enFlat)
  const total = keys.length
  const untranslated: string[] = []
  let translated = 0
  for (const k of keys) {
    const effective = draft[k] ?? targetFlat[k] ?? ''
    if (effective.length > 0 && effective !== enFlat[k]) translated += 1
    else untranslated.push(k)
  }
  const pct = total > 0 ? Math.round((translated / total) * 100) : 100
  return { total, translated, untranslated, pct }
}

export function draftStorageKey(locale: Locale): string {
  return `md-bridge:i18n-draft:${locale}`
}

export function loadDraft(locale: Locale): Record<string, string> {
  try {
    const raw = window.localStorage.getItem(draftStorageKey(locale))
    if (!raw) return {}
    const parsed: unknown = JSON.parse(raw)
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed)
      ? (parsed as Record<string, string>)
      : {}
  } catch {
    return {}
  }
}

export function saveDraft(locale: Locale, draft: Record<string, string>): void {
  try {
    window.localStorage.setItem(draftStorageKey(locale), JSON.stringify(draft))
  } catch {
    /* storage full or unavailable: drafts are best-effort, never fatal */
  }
}

type Nested = { [k: string]: string | Nested }

function buildNested(draft: Record<string, string>): Nested {
  const root: Nested = {}
  for (const [path, value] of Object.entries(draft)) {
    if (!value) continue
    const parts = path.split('.')
    let node = root
    for (let i = 0; i < parts.length - 1; i += 1) {
      const p = parts[i]
      if (typeof node[p] !== 'object' || node[p] == null) node[p] = {}
      node = node[p] as Nested
    }
    node[parts[parts.length - 1]] = value
  }
  return root
}

function tsString(value: string): string {
  return `'${value.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\n/g, '\\n')}'`
}

function renderTs(node: Nested, indent = '  '): string {
  const inner = Object.entries(node)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => {
      const key = /^[A-Za-z_$][\w$]*$/.test(k) ? k : tsString(k)
      const val = typeof v === 'string' ? tsString(v) : renderTs(v, `${indent}  `)
      return `${indent}${key}: ${val},`
    })
    .join('\n')
  return `{\n${inner}\n${indent.slice(2)}}`
}

/** Render the drafted keys as a nested TypeScript object literal the
 *  contributor merges into the locale block of dictionaries.ts. The object
 *  part parses back to the nested draft, so it is exact, not a fake diff. */
export function serializeDraftAsTs(locale: Locale, draft: Record<string, string>): string {
  const nested = buildNested(draft)
  if (Object.keys(nested).length === 0) return `// no translations drafted for "${locale}" yet`
  return `// Merge into the "${locale}" block of apps/web/src/i18n/dictionaries.ts\n${renderTs(nested)}`
}

export function serializeDraftAsJson(draft: Record<string, string>): string {
  return JSON.stringify(buildNested(draft), null, 2)
}
