import { useEffect, useState } from 'react'
import { fetchFormats, type Format } from '../lib/api'

type Status = 'loading' | 'ready' | 'error'

interface FormatsState {
  formats: Format[]
  status: Status
  error: string | null
}

// One fetch per page lifetime, shared across hook instances. No invalidation: a
// pair added to the server registry shows after a refresh, matching the
// restart-to-reload model the themes registry already uses (#60).
let cache: Promise<Format[]> | null = null

function load(): Promise<Format[]> {
  if (!cache) cache = fetchFormats()
  return cache
}

/** Reset the in-memory cache. Test-only; the app never re-fetches in a session. */
export function _resetFormatsCacheForTests(): void {
  cache = null
}

export function useFormats(): FormatsState {
  const [state, setState] = useState<FormatsState>({
    formats: [],
    status: 'loading',
    error: null,
  })

  useEffect(() => {
    let active = true
    load()
      .then((formats) => {
        if (active) setState({ formats, status: 'ready', error: null })
      })
      .catch((err: unknown) => {
        // A failed fetch is not fatal: the matrix simply renders nothing and the
        // curated cards above it stay. Let a later mount retry rather than
        // caching the failure.
        cache = null
        if (active) {
          setState({
            formats: [],
            status: 'error',
            error: err instanceof Error ? err.message : 'Failed to load formats',
          })
        }
      })
    return () => {
      active = false
    }
  }, [])

  return state
}
