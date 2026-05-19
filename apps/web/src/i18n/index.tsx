/* eslint-disable react-refresh/only-export-components --
 * Co-locating the provider, the hook, and the types in a single entry-point
 * keeps the i18n surface easy to discover. The fast-refresh penalty only
 * affects HMR on saves to this file, which the team accepts. */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { DICTIONARIES, LOCALES, type Dictionary, type Locale } from './dictionaries'

const STORAGE_KEY = 'md-bridge:locale'
const SUPPORTED_LOCALES = LOCALES.map(({ code }) => code)

function isSupportedLocale(value: string | null): value is Locale {
  return SUPPORTED_LOCALES.includes(value as Locale)
}

function detectInitialLocale(): Locale {
  if (typeof window === 'undefined') return 'en'
  const stored = window.localStorage.getItem(STORAGE_KEY)
  if (isSupportedLocale(stored)) return stored
  const nav = window.navigator?.language?.toLowerCase() ?? ''
  const browserLocale = nav.split(/[-_]/)[0]
  if (isSupportedLocale(browserLocale)) return browserLocale
  return 'en'
}

interface I18nContextValue {
  locale: Locale
  t: Dictionary
  setLocale: (locale: Locale) => void
  locales: typeof LOCALES
}

const I18nContext = createContext<I18nContextValue | null>(null)

export function I18nProvider({
  children,
  initialLocale,
}: {
  children: ReactNode
  initialLocale?: Locale
}) {
  const [locale, setLocaleState] = useState<Locale>(initialLocale ?? detectInitialLocale)

  useEffect(() => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(STORAGE_KEY, locale)
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('lang', locale === 'pt' ? 'pt-BR' : locale)
    }
  }, [locale])

  const setLocale = useCallback((next: Locale) => setLocaleState(next), [])

  const value = useMemo<I18nContextValue>(
    () => ({ locale, t: DICTIONARIES[locale], setLocale, locales: LOCALES }),
    [locale, setLocale],
  )

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useTranslation(): I18nContextValue {
  const ctx = useContext(I18nContext)
  if (!ctx) {
    throw new Error('useTranslation must be used within an I18nProvider')
  }
  return ctx
}

export type { Locale, Dictionary }
