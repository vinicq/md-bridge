/* Conversion presets (#62).
 *
 * A browser-local, per-format-pair list of named option bundles under
 * `md-bridge:presets:<pair>`. Metadata only, same no-server-persistence stance
 * as the rest of the app. Unlike history (which FIFO-evicts silently), a preset
 * is user-named data: the cap is a hard stop, never a silent eviction. */
import type { MdToPdfOptions } from './api'
import type { ConversionPair } from './history'

export const PRESET_CAP = 12

export interface Preset {
  id: string
  name: string
  pair: ConversionPair
  /** The savable bundle. Today only md-to-pdf has anything here (theme +
   *  custom_css); pdf-to-md options are not surfaced yet (see #453). */
  options: MdToPdfOptions
  /** epoch ms. */
  createdAt: number
}

function keyFor(pair: ConversionPair): string {
  return `md-bridge:presets:${pair}`
}

function isPreset(value: unknown): value is Preset {
  if (typeof value !== 'object' || value === null) return false
  const p = value as Record<string, unknown>
  return (
    typeof p.id === 'string' &&
    p.id.length > 0 &&
    typeof p.name === 'string' &&
    p.name.length > 0 &&
    (p.pair === 'pdf-to-md' || p.pair === 'md-to-pdf') &&
    isValidOptions(p.options) &&
    typeof p.createdAt === 'number' &&
    Number.isFinite(p.createdAt)
  )
}

// Validate the option field types, not just "is an object": an imported file
// with `options: { custom_css: 42 }` would otherwise be accepted and later post
// an invalid payload to /api/md-to-pdf. Only the fields we actually save today
// are checked; each is optional but, when present, must have the right type.
function isValidOptions(value: unknown): value is MdToPdfOptions {
  if (typeof value !== 'object' || value === null) return false
  const o = value as Record<string, unknown>
  if ('theme' in o && typeof o.theme !== 'string') return false
  if ('custom_css' in o && typeof o.custom_css !== 'string') return false
  if ('lang' in o && typeof o.lang !== 'string') return false
  if ('page_setup' in o && o.page_setup !== null && typeof o.page_setup !== 'object') return false
  return true
}

function persist(pair: ConversionPair, presets: Preset[]): void {
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(keyFor(pair), JSON.stringify(presets))
  }
}

/** Read the presets for a pair, dropping any corrupt entries. */
export function readPresets(pair: ConversionPair): Preset[] {
  if (typeof window === 'undefined') return []
  const raw = window.localStorage.getItem(keyFor(pair))
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? (parsed.filter(isPreset) as Preset[]).slice(0, PRESET_CAP) : []
  } catch {
    return []
  }
}

/** Save a preset. A name already in use is replaced in place (names are unique
 *  identities, the same way import treats them, so every UI state round-trips
 *  through export/import). Returns the new list, or null when the name is new
 *  and the cap is already hit - the caller then asks the user to delete one. */
export function addPreset(pair: ConversionPair, preset: Preset): Preset[] | null {
  const current = readPresets(pair)
  const existing = current.findIndex((p) => p.name === preset.name)
  if (existing >= 0) {
    const next = [...current]
    next[existing] = preset
    persist(pair, next)
    return next
  }
  if (current.length >= PRESET_CAP) return null
  const next = [...current, preset]
  persist(pair, next)
  return next
}

export function removePreset(pair: ConversionPair, id: string): Preset[] {
  const next = readPresets(pair).filter((p) => p.id !== id)
  persist(pair, next)
  return next
}

export function clearPresets(pair: ConversionPair): void {
  if (typeof window !== 'undefined') window.localStorage.removeItem(keyFor(pair))
}

/** Parse an imported file. Returns the valid presets, or null when the payload
 *  is not JSON or carries no valid preset (the caller shows a toast). Accepts a
 *  single preset object or an array. */
export function parseImport(raw: string): Preset[] | null {
  let parsed: unknown
  try {
    parsed = JSON.parse(raw)
  } catch {
    return null
  }
  const arr = Array.isArray(parsed) ? parsed : [parsed]
  const valid = arr.filter(isPreset) as Preset[]
  return valid.length > 0 ? valid : null
}

export interface ImportResult {
  presets: Preset[]
  imported: number
  ignored: number
}

/** Merge imported presets into a pair, deduping by name (import updates an
 *  existing name in place) and honoring the cap. Returns the merged list plus
 *  how many new names were added vs dropped for the cap. */
export function importPresets(pair: ConversionPair, incoming: Preset[]): ImportResult {
  const byName = new Map<string, Preset>(readPresets(pair).map((p) => [p.name, p]))
  let imported = 0
  let ignored = 0
  for (const p of incoming) {
    const normalized: Preset = { ...p, pair }
    if (byName.has(p.name)) {
      byName.set(p.name, normalized) // update in place, not a new slot
      continue
    }
    if (byName.size >= PRESET_CAP) {
      ignored += 1
      continue
    }
    byName.set(p.name, normalized)
    imported += 1
  }
  const merged = [...byName.values()]
  persist(pair, merged)
  return { presets: merged, imported, ignored }
}

/** Pretty-printed JSON of every preset for a pair (the Export payload). */
export function serializePresets(pair: ConversionPair): string {
  return JSON.stringify(readPresets(pair), null, 2)
}
