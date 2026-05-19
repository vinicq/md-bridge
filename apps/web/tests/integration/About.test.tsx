import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { About } from '../../src/pages/About'
import { I18nProvider } from '../../src/i18n'

function renderAbout(locale: 'en' | 'pt' = 'en') {
  return render(
    <I18nProvider initialLocale={locale}>
      <MemoryRouter>
        <About />
      </MemoryRouter>
    </I18nProvider>,
  )
}

describe('About page', () => {
  it('renders the title, intro and the three sections in English', () => {
    renderAbout()
    expect(screen.getByRole('heading', { level: 1, name: /about md-bridge/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 2, name: /how it works/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 2, name: /known limits/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 2, name: /open source/i })).toBeInTheDocument()
  })

  it('renders each known limit as a list item', () => {
    renderAbout()
    const items = screen.getAllByRole('listitem')
    expect(items.length).toBeGreaterThanOrEqual(3)
    const text = items.map((li) => li.textContent ?? '').join(' | ')
    expect(text).toMatch(/ocr/i)
    expect(text).toMatch(/cells merged/i)
    expect(text).toMatch(/headers and footers/i)
  })

  it('honors the PT locale for the title', () => {
    renderAbout('pt')
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/sobre o md-bridge/i)
  })
})
