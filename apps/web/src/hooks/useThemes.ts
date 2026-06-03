import { useEffect, useState } from 'react'
import { fetchThemes, type Theme } from '../lib/api'

type Status = 'loading' | 'ready' | 'error'

interface ThemesState {
  themes: Theme[]
  status: Status
  error: string | null
}

// The picker must always have at least one tile to render. If the API is down
// or returns nothing, fall back to the single built-in default so the page
// stays usable (the backend renders `default` when no theme is selected).
const DEFAULT_FALLBACK: Theme = {
  slug: 'default',
  name: 'Default',
  description: '',
  family: 'general',
}

// One fetch per page lifetime, shared across every hook instance. There is no
// invalidation: a theme added on the server shows after a page refresh, which
// matches the registry's restart-to-reload deployment model (#23).
let cache: Promise<Theme[]> | null = null

function load(): Promise<Theme[]> {
  if (!cache) {
    cache = fetchThemes().then((list) => (list.length > 0 ? list : [DEFAULT_FALLBACK]))
  }
  return cache
}

/** Reset the in-memory cache. Test-only; the app never re-fetches in a session. */
export function _resetThemesCacheForTests(): void {
  cache = null
}

export function useThemes(): ThemesState {
  const [state, setState] = useState<ThemesState>({
    themes: [DEFAULT_FALLBACK],
    status: 'loading',
    error: null,
  })

  useEffect(() => {
    let active = true
    load()
      .then((themes) => {
        if (active) setState({ themes, status: 'ready', error: null })
      })
      .catch((err: unknown) => {
        // A failed fetch is not fatal: keep the default tile and surface the
        // reason so the caller can decide whether to show it.
        cache = null // let a later mount retry rather than caching the failure
        if (active) {
          setState({
            themes: [DEFAULT_FALLBACK],
            status: 'error',
            error: err instanceof Error ? err.message : 'Failed to load themes',
          })
        }
      })
    return () => {
      active = false
    }
  }, [])

  return state
}
