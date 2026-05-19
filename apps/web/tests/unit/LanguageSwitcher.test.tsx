import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { LanguageSwitcher } from '../../src/components/LanguageSwitcher'
import { I18nProvider, useTranslation } from '../../src/i18n'

function Inspector() {
  const { t } = useTranslation()
  return <p data-testid="probe">{t.nav.about}</p>
}

beforeEach(() => {
  window.localStorage.clear()
})

afterEach(() => {
  window.localStorage.clear()
})

describe('LanguageSwitcher', () => {
  it('renders one button per locale with the active one pressed', () => {
    render(
      <I18nProvider initialLocale="en">
        <LanguageSwitcher />
      </I18nProvider>,
    )
    const en = screen.getByRole('button', { name: /english/i })
    const pt = screen.getByRole('button', { name: /portugu/i })
    const es = screen.getByRole('button', { name: /español/i })
    expect(en).toHaveAttribute('aria-pressed', 'true')
    expect(pt).toHaveAttribute('aria-pressed', 'false')
    expect(es).toHaveAttribute('aria-pressed', 'false')
  })

  it('flips the active locale on click and updates dependent text', async () => {
    render(
      <I18nProvider initialLocale="en">
        <LanguageSwitcher />
        <Inspector />
      </I18nProvider>,
    )
    expect(screen.getByTestId('probe')).toHaveTextContent('About')
    await userEvent.click(screen.getByRole('button', { name: /español/i }))
    expect(screen.getByTestId('probe')).toHaveTextContent('Acerca de')
  })

  it('persists the chosen locale to localStorage', async () => {
    render(
      <I18nProvider initialLocale="en">
        <LanguageSwitcher />
      </I18nProvider>,
    )
    await userEvent.click(screen.getByRole('button', { name: /español/i }))
    expect(window.localStorage.getItem('md-bridge:locale')).toBe('es')
  })
})
