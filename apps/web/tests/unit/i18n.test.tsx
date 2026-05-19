import { act, render, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { I18nProvider, useTranslation } from '../../src/i18n'

beforeEach(() => {
  window.localStorage.clear()
})

afterEach(() => {
  window.localStorage.clear()
})

describe('I18nProvider', () => {
  it('defaults to English when no localStorage value or PT navigator', () => {
    const { result } = renderHook(() => useTranslation(), {
      wrapper: ({ children }) => <I18nProvider initialLocale="en">{children}</I18nProvider>,
    })
    expect(result.current.locale).toBe('en')
    expect(result.current.t.nav.about).toBe('About')
  })

  it('honors an explicit initialLocale prop over auto-detection', () => {
    const { result } = renderHook(() => useTranslation(), {
      wrapper: ({ children }) => <I18nProvider initialLocale="es">{children}</I18nProvider>,
    })
    expect(result.current.locale).toBe('es')
    expect(result.current.t.nav.about).toBe('Acerca de')
  })

  it('persists the locale change to localStorage', async () => {
    const { result } = renderHook(() => useTranslation(), {
      wrapper: ({ children }) => <I18nProvider initialLocale="en">{children}</I18nProvider>,
    })
    await act(async () => {
      result.current.setLocale('pt')
    })
    expect(window.localStorage.getItem('md-bridge:locale')).toBe('pt')
    expect(result.current.locale).toBe('pt')
  })

  it('reads a stored locale on mount', () => {
    window.localStorage.setItem('md-bridge:locale', 'pt')
    const { result } = renderHook(() => useTranslation(), {
      wrapper: ({ children }) => <I18nProvider>{children}</I18nProvider>,
    })
    expect(result.current.locale).toBe('pt')
  })

  it('exposes the available locales list', () => {
    const { result } = renderHook(() => useTranslation(), {
      wrapper: ({ children }) => <I18nProvider initialLocale="en">{children}</I18nProvider>,
    })
    const codes = result.current.locales.map((l) => l.code)
    expect(codes).toEqual(['en', 'pt', 'es'])
  })

  it('throws when useTranslation is used outside the provider', () => {
    function Bad() {
      useTranslation()
      return null
    }
    const spy = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    expect(() => render(<Bad />)).toThrow(/I18nProvider/)
    spy.mockRestore()
  })
})
