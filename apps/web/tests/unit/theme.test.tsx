import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, beforeEach, afterEach } from 'vitest'
import { ThemeProvider, useTheme } from '../../src/theme'

describe('ThemeProvider & useTheme', () => {
  beforeEach(() => {
    window.localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })

  afterEach(() => {
    window.localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })

  it('defaults to light when no preference exists', () => {
    function Inspector() {
      const { theme } = useTheme()
      return <span data-testid="theme">{theme}</span>
    }
    render(
      <ThemeProvider>
        <Inspector />
      </ThemeProvider>,
    )
    expect(screen.getByTestId('theme')).toHaveTextContent('light')
  })

  it('toggles between light and dark', async () => {
    function Toggle() {
      const { theme, toggleTheme } = useTheme()
      return (
        <button onClick={toggleTheme} data-testid="toggle">
          {theme}
        </button>
      )
    }
    render(
      <ThemeProvider>
        <Toggle />
      </ThemeProvider>,
    )
    expect(screen.getByTestId('toggle')).toHaveTextContent('light')
    await userEvent.click(screen.getByTestId('toggle'))
    expect(screen.getByTestId('toggle')).toHaveTextContent('dark')
  })

  it('persists theme to localStorage', async () => {
    function Toggle() {
      const { toggleTheme } = useTheme()
      return <button onClick={toggleTheme}>Toggle</button>
    }
    render(
      <ThemeProvider>
        <Toggle />
      </ThemeProvider>,
    )
    await userEvent.click(screen.getByRole('button', { name: /toggle/i }))
    expect(window.localStorage.getItem('md-bridge:theme')).toBe('dark')
  })

  it('reads initial theme from localStorage', () => {
    window.localStorage.setItem('md-bridge:theme', 'dark')
    function Inspector() {
      const { theme } = useTheme()
      return <span data-testid="theme">{theme}</span>
    }
    render(
      <ThemeProvider>
        <Inspector />
      </ThemeProvider>,
    )
    expect(screen.getByTestId('theme')).toHaveTextContent('dark')
  })
})
