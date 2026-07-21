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
    document.documentElement.style.removeProperty('--c-accent')
  })
  afterEach(() => {
    window.localStorage.clear()
    document.documentElement.style.removeProperty('--c-accent')
  })

  it('resets every md-bridge:* key and reloads', async () => {
    const reload = vi.fn()
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...window.location, reload },
    })
    window.localStorage.setItem('md-bridge:prefs', '{"accent":"#123456"}')
    window.localStorage.setItem('md-bridge:history', '[]')
    window.localStorage.setItem('md-bridge:presets', '{}')
    window.localStorage.setItem('unrelated', 'keep')

    renderPage()
    await userEvent.click(screen.getByRole('button', { name: /reset all preferences/i }))

    expect(window.localStorage.getItem('md-bridge:prefs')).toBeNull()
    expect(window.localStorage.getItem('md-bridge:history')).toBeNull()
    expect(window.localStorage.getItem('md-bridge:presets')).toBeNull()
    expect(window.localStorage.getItem('unrelated')).toBe('keep')
    expect(reload).toHaveBeenCalled()
  })

  it('writes the chosen accent to the --c-accent root variable', async () => {
    renderPage()
    // The "Green" swatch is exposed by its accessible name.
    await userEvent.click(screen.getByRole('radio', { name: /green/i }))
    expect(document.documentElement.style.getPropertyValue('--c-accent')).toBe('#2e7d4a')
    expect(JSON.parse(window.localStorage.getItem('md-bridge:prefs')!).accent).toBe('#2e7d4a')
  })
})
