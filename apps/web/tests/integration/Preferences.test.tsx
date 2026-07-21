import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { App } from '../../src/App'
import { Home } from '../../src/pages/Home'
import { Preferences } from '../../src/pages/Preferences'
import { I18nProvider } from '../../src/i18n'
import { ThemeProvider } from '../../src/theme'
import { _resetThemesCacheForTests } from '../../src/hooks/useThemes'

vi.mock('../../src/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../src/lib/api')>()),
  fetchThemes: vi.fn().mockResolvedValue([
    { slug: 'default', name: 'Default', description: '', family: 'general' },
    { slug: 'academic', name: 'Academic', description: '', family: 'serif' },
  ]),
}))

function renderApp(initialPath = '/preferences') {
  return render(
    <ThemeProvider>
      <I18nProvider initialLocale="en">
        <MemoryRouter initialEntries={[initialPath]}>
          <Routes>
            <Route path="/" element={<App />}>
              <Route index element={<Home />} />
              <Route path="preferences" element={<Preferences />} />
            </Route>
          </Routes>
        </MemoryRouter>
      </I18nProvider>
    </ThemeProvider>,
  )
}

describe('Preferences page integration (#64)', () => {
  beforeEach(() => {
    window.localStorage.clear()
    _resetThemesCacheForTests()
  })
  afterEach(() => {
    vi.restoreAllMocks()
    window.localStorage.clear()
  })

  it('renders the three sections, the theme select and the privacy badge', async () => {
    renderApp('/preferences')
    expect(screen.getByRole('heading', { level: 1, name: /preferences/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 2, name: /defaults/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 2, name: /ui/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 2, name: /privacy/i })).toBeInTheDocument()

    // The default-PDF-theme select is populated from the (mocked) catalog.
    expect(await screen.findByRole('option', { name: 'Academic' })).toBeInTheDocument()

    // The privacy badge affirms the no-telemetry contract.
    expect(screen.getByText(/no telemetry\. no cookies\. no accounts\./i)).toBeInTheDocument()
  })

  it('reaches the page from the header link', async () => {
    renderApp('/')
    const nav = screen.getByRole('navigation', { name: /main navigation/i })
    await userEvent.click(within(nav).getByRole('link', { name: /^preferences$/i }))
    expect(screen.getByRole('heading', { level: 1, name: /preferences/i })).toBeInTheDocument()
  })
})
