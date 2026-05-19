import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from '../../src/App'
import { Home } from '../../src/pages/Home'
import { About } from '../../src/pages/About'
import { I18nProvider } from '../../src/i18n'

afterEach(() => {
  vi.restoreAllMocks()
  window.localStorage.clear()
})

function renderApp(initialPath = '/') {
  return render(
    <I18nProvider initialLocale="en">
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/" element={<App />}>
            <Route index element={<Home />} />
            <Route path="about" element={<About />} />
          </Route>
        </Routes>
      </MemoryRouter>
    </I18nProvider>,
  )
}

describe('Navigation + LanguageSwitcher integration', () => {
  it('navigates from Home to About via the header link', async () => {
    renderApp('/')
    expect(screen.getByRole('heading', { level: 1, name: /convert pdf and markdown locally/i })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('link', { name: /^about$/i }))
    expect(screen.getByRole('heading', { level: 1, name: /about md-bridge/i })).toBeInTheDocument()
  })

  it('flips the whole UI to Portuguese when the language toggle is used', async () => {
    renderApp('/')
    await userEvent.click(screen.getByRole('button', { name: /portugu/i }))
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/converta pdf e markdown local/i)
    expect(screen.getByRole('link', { name: /^sobre$/i })).toBeInTheDocument()
  })

  it('flips the whole UI to Spanish when the language toggle is used', async () => {
    renderApp('/')
    await userEvent.click(screen.getByRole('button', { name: /español/i }))
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      /convierte pdf y markdown localmente/i,
    )
    expect(screen.getByRole('link', { name: /^acerca de$/i })).toBeInTheDocument()
  })
})
