import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { Preferences } from '../../src/pages/Preferences'
import { I18nProvider } from '../../src/i18n'
import { ThemeProvider } from '../../src/theme'
import { _resetThemesCacheForTests } from '../../src/hooks/useThemes'

vi.mock('../../src/lib/api', () => ({
  fetchThemes: vi.fn().mockResolvedValue([
    { slug: 'default', name: 'Default', description: '', family: 'general' },
    { slug: 'academic', name: 'Academic', description: '', family: 'serif' },
  ]),
}))

function mockPrefersReducedMotion(matches: boolean) {
  Object.defineProperty(window, 'matchMedia', {
    configurable: true,
    value: (query: string) => ({
      matches,
      media: query,
      addEventListener: () => {},
      removeEventListener: () => {},
    }),
  })
}

function renderPage() {
  return render(
    <ThemeProvider>
      <I18nProvider initialLocale="en">
        <Preferences />
      </I18nProvider>
    </ThemeProvider>,
  )
}

describe('Preferences page (#64)', () => {
  beforeEach(() => {
    window.localStorage.clear()
    _resetThemesCacheForTests()
    mockPrefersReducedMotion(false)
    document.documentElement.removeAttribute('data-reduce-motion')
  })
  afterEach(() => {
    window.localStorage.clear()
    document.documentElement.removeAttribute('data-reduce-motion')
  })

  it('resets every md-bridge:* key and reloads', async () => {
    const reload = vi.fn()
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...window.location, reload },
    })
    window.localStorage.setItem('md-bridge:prefs', '{"defaultPdfTheme":"academic"}')
    window.localStorage.setItem('md-bridge:history', '[]')
    window.localStorage.setItem('unrelated', 'keep')

    renderPage()
    await userEvent.click(screen.getByRole('button', { name: /reset all preferences/i }))

    expect(window.localStorage.getItem('md-bridge:prefs')).toBeNull()
    expect(window.localStorage.getItem('md-bridge:history')).toBeNull()
    expect(window.localStorage.getItem('unrelated')).toBe('keep')
    expect(reload).toHaveBeenCalled()
  })

  it('turning on reduce-motion forces the flag and persists true', async () => {
    renderPage()
    const toggle = screen.getByRole('switch', { name: /reduce motion/i })
    expect(toggle).toHaveAttribute('aria-checked', 'false')
    await userEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-checked', 'true')
    expect(document.documentElement.getAttribute('data-reduce-motion')).toBe('true')
    expect(JSON.parse(window.localStorage.getItem('md-bridge:prefs')!).reduceMotion).toBe(true)
  })

  it('reduce-motion switch reads On from the OS when the preference follows it', () => {
    // No stored override (null) but the OS asks for reduced motion: the switch
    // must announce On, not lie with Off while the @media rule reduces motion.
    mockPrefersReducedMotion(true)
    renderPage()
    expect(screen.getByRole('switch', { name: /reduce motion/i })).toHaveAttribute(
      'aria-checked',
      'true',
    )
  })
})
