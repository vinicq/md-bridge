/* React binding over the prefs store (#64). Holds the merged preferences in
 * state and, on every change, persists them and re-applies the document-level
 * effects (accent variable, reduce-motion flag). */
import { useCallback, useState } from 'react'
import { applyPrefsToDocument, readPrefs, writePrefs, type Prefs } from '../lib/prefs'

export function usePrefs() {
  const [prefs, setPrefs] = useState<Prefs>(readPrefs)

  const set = useCallback((patch: Partial<Prefs>) => {
    const next = writePrefs(patch)
    applyPrefsToDocument(next)
    setPrefs(next)
  }, [])

  return { prefs, set }
}
