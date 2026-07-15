import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, beforeEach, afterEach } from 'vitest'
import { I18nProvider } from '../../src/i18n'
import { ThemeProvider } from '../../src/theme'
import { ThemeToggle } from '../../src/components/ThemeToggle'

function renderToggle(locale: 'en' | 'pt' | 'es' = 'en') {
  return render(
    <I18nProvider initialLocale={locale}>
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    </I18nProvider>,
  )
}

describe('ThemeToggle', () => {
  beforeEach(() => {
    window.localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })

  afterEach(() => {
    window.localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })

  it('renders a button with a sun icon when in light mode', () => {
    renderToggle()
    const btn = screen.getByRole('button', { name: /switch to dark mode/i })
    expect(btn).toBeInTheDocument()
    expect(btn).toHaveAttribute('aria-pressed', 'false')
  })

  it('toggles to dark mode on click and shows moon icon', async () => {
    renderToggle()
    const btn = screen.getByRole('button', { name: /switch to dark mode/i })
    await userEvent.click(btn)
    expect(screen.getByRole('button', { name: /switch to light mode/i })).toHaveAttribute('aria-pressed', 'true')
  })

  it('persists toggled theme to localStorage', async () => {
    renderToggle()
    await userEvent.click(screen.getByRole('button', { name: /switch to dark mode/i }))
    expect(window.localStorage.getItem('md-bridge:theme')).toBe('dark')
  })

  it('localizes the toggle label (pt)', () => {
    renderToggle('pt')
    expect(screen.getByRole('button', { name: 'Mudar para o tema escuro' })).toBeInTheDocument()
  })
})
