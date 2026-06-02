import { fireEvent, render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import { LanguageWorkshop } from '../../src/pages/LanguageWorkshop'
import { I18nProvider } from '../../src/i18n'

function renderWorkshop(locale: 'en' | 'pt' | 'es' = 'en') {
  return render(
    <I18nProvider initialLocale={locale}>
      <MemoryRouter>
        <LanguageWorkshop />
      </MemoryRouter>
    </I18nProvider>,
  )
}

beforeEach(() => {
  window.localStorage.clear()
})

describe('Language Workshop page', () => {
  it('renders the title and a captioned three-column table', () => {
    renderWorkshop()
    expect(
      screen.getByRole('heading', { level: 1, name: /language workshop/i }),
    ).toBeInTheDocument()
    expect(screen.getAllByRole('columnheader')).toHaveLength(3)
    // The <caption> gives the table its accessible name.
    expect(
      screen.getByRole('table', { name: /every translation key/i }),
    ).toBeInTheDocument()
  })

  it('shows a progressbar per target locale with a numeric value', () => {
    renderWorkshop()
    const bars = screen.getAllByRole('progressbar')
    expect(bars).toHaveLength(2) // pt, es
    for (const bar of bars) {
      expect(Number.isNaN(Number(bar.getAttribute('aria-valuenow')))).toBe(false)
    }
  })

  it('renders editable rows whose inputs each have an accessible name', () => {
    renderWorkshop()
    const inputs = screen.getAllByRole('textbox')
    expect(inputs.length).toBeGreaterThan(10)
    for (const input of inputs.slice(0, 5)) {
      expect(input).toHaveAccessibleName()
    }
  })

  it('offers the non-English locales as translation targets', () => {
    renderWorkshop()
    const select = screen.getByRole('combobox', { name: /locale to translate/i })
    const values = within(select)
      .getAllByRole('option')
      .map((o) => (o as HTMLOptionElement).value)
      .sort()
    expect(values).toEqual(['es', 'pt'])
  })

  it('persists a draft edit to localStorage under the target locale key', () => {
    renderWorkshop() // default target is the first non-English locale (pt)
    const input = screen.getAllByRole('textbox')[0]
    fireEvent.change(input, { target: { value: 'minha traducao unica de teste' } })
    const stored = window.localStorage.getItem('md-bridge:i18n-draft:pt') ?? ''
    expect(stored).toContain('minha traducao unica de teste')
  })

  it('localizes its own chrome in PT (no English leak)', () => {
    renderWorkshop('pt')
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/oficina de idiomas/i)
  })
})
