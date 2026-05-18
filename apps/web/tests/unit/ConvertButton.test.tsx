import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ConvertButton } from '../../src/components/ConvertButton'
import { I18nProvider } from '../../src/i18n'

function wrap(node: React.ReactNode) {
  return <I18nProvider initialLocale="en">{node}</I18nProvider>
}

describe('ConvertButton', () => {
  it('shows the idle label and is clickable by default', async () => {
    const onClick = vi.fn()
    render(wrap(<ConvertButton status="idle" onClick={onClick} />))
    const btn = screen.getByRole('button', { name: /convert/i })
    await userEvent.click(btn)
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('renders the loading state and disables interaction', async () => {
    const onClick = vi.fn()
    render(wrap(<ConvertButton status="loading" onClick={onClick} />))
    const btn = screen.getByRole('button', { name: /converting/i })
    expect(btn).toBeDisabled()
    expect(btn).toHaveAttribute('aria-busy', 'true')
    await userEvent.click(btn)
    expect(onClick).not.toHaveBeenCalled()
  })

  it('uses custom labels when provided', () => {
    render(
      wrap(
        <ConvertButton
          status="loading"
          onClick={() => undefined}
          labels={{ loading: 'Working hard' }}
        />,
      ),
    )
    expect(screen.getByRole('button', { name: /working hard/i })).toBeInTheDocument()
  })

  it('flips to the ghost variant on error', () => {
    render(wrap(<ConvertButton status="error" onClick={() => undefined} />))
    expect(screen.getByRole('button')).toHaveClass('btn--ghost')
  })

  it('honors the disabled prop in idle state', async () => {
    const onClick = vi.fn()
    render(wrap(<ConvertButton status="idle" onClick={onClick} disabled />))
    const btn = screen.getByRole('button')
    expect(btn).toBeDisabled()
    await userEvent.click(btn)
    expect(onClick).not.toHaveBeenCalled()
  })
})
