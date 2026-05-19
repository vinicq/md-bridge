import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { Home } from '../../src/pages/Home'
import { I18nProvider } from '../../src/i18n'

function renderHome() {
  return render(
    <I18nProvider initialLocale="en">
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    </I18nProvider>,
  )
}

describe('Home page', () => {
  it('renders the hero headline in English', () => {
    renderHome()
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      /convert pdf and markdown locally/i,
    )
  })

  it('renders both feature cards with their CTAs', () => {
    renderHome()
    expect(screen.getByRole('heading', { level: 2, name: /pdf → markdown/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 2, name: /markdown → pdf/i })).toBeInTheDocument()

    const ctaPdf = screen.getByRole('link', { name: /convert a pdf/i })
    const ctaMd = screen.getByRole('link', { name: /generate a pdf/i })
    expect(ctaPdf).toHaveAttribute('href', '/convert/pdf-to-md')
    expect(ctaMd).toHaveAttribute('href', '/convert/md-to-pdf')
  })

  it('flips to Portuguese strings when the locale changes', () => {
    render(
      <I18nProvider initialLocale="pt">
        <MemoryRouter>
          <Home />
        </MemoryRouter>
      </I18nProvider>,
    )
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/converta pdf e markdown local/i)
  })

  it('flips to Spanish strings when the locale changes', () => {
    render(
      <I18nProvider initialLocale="es">
        <MemoryRouter>
          <Home />
        </MemoryRouter>
      </I18nProvider>,
    )
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      /convierte pdf y markdown localmente/i,
    )
  })
})
