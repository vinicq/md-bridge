/* React binding over the preset store (#62). Presets are fully serializable
 * (no session-scoped blobs, unlike history), so the state is a plain mirror of
 * localStorage seeded on mount. */
import { useCallback, useState } from 'react'
import type { ConversionPair } from '../lib/history'
import {
  addPreset,
  clearPresets,
  importPresets,
  PRESET_CAP,
  readPresets,
  removePreset,
  type ImportResult,
  type Preset,
} from '../lib/presets'

export function usePresets(pair: ConversionPair) {
  const [presets, setPresets] = useState<Preset[]>(() => readPresets(pair))

  // Returns false when the cap is already hit (the caller surfaces the warning);
  // presets are user-named data and are never silently evicted.
  const save = useCallback(
    (preset: Preset): boolean => {
      const next = addPreset(pair, preset)
      if (next === null) return false
      setPresets(next)
      return true
    },
    [pair],
  )

  const remove = useCallback((id: string) => setPresets(removePreset(pair, id)), [pair])

  const clear = useCallback(() => {
    clearPresets(pair)
    setPresets([])
  }, [pair])

  const importFrom = useCallback(
    (incoming: Preset[]): ImportResult => {
      const result = importPresets(pair, incoming)
      setPresets(result.presets)
      return result
    },
    [pair],
  )

  return { presets, save, remove, clear, importFrom, atCap: presets.length >= PRESET_CAP }
}
