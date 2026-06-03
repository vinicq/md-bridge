import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ThemePicker } from '../../src/components/ThemePicker'
import type { Theme } from '../../src/lib/api'

const THEMES: Theme[] = [
  { slug: 'default', name: 'Default', description: '', family: 'general' },
  { slug: 'academic', name: 'Academic', description: 'Serif.', family: 'serif' },
  { slug: 'business', name: 'Business', description: 'Accent.', family: 'sans' },
]

function renderPicker(value: string, onChange = vi.fn(), disabled = false) {
  render(
    <ThemePicker
      themes={THEMES}
      value={value}
      onChange={onChange}
      label="Theme"
      browseLabel="Browse all themes →"
      browseHref="/themes"
      disabled={disabled}
    />,
  )
  return onChange
}

describe('ThemePicker', () => {
  it('renders one tile per theme from the list', () => {
    renderPicker('default')
    expect(screen.getAllByRole('radio')).toHaveLength(THEMES.length)
    expect(screen.getByText('Academic')).toBeInTheDocument()
    expect(screen.getByText('Business')).toBeInTheDocument()
  })

  it('marks the selected tile active and checks its radio', () => {
    renderPicker('academic')
    const academic = screen.getByRole('radio', { name: /academic/i })
    expect(academic).toBeChecked()
    // The active class lands on the tile label wrapping the checked radio.
    expect(academic.closest('.theme-tile')).toHaveClass('is-active')
  })

  it('calls onChange with the slug when a tile is picked', async () => {
    const onChange = renderPicker('default')
    await userEvent.click(screen.getByRole('radio', { name: /business/i }))
    expect(onChange).toHaveBeenCalledWith('business')
  })

  it('locks selection when disabled (e.g. while converting)', async () => {
    const onChange = renderPicker('default', vi.fn(), true)
    const business = screen.getByRole('radio', { name: /business/i })
    expect(business).toBeDisabled()
    await userEvent.click(business)
    expect(onChange).not.toHaveBeenCalled()
  })

  it('points the browse link at the deep library route', () => {
    renderPicker('default')
    expect(screen.getByRole('link', { name: /browse all themes/i })).toHaveAttribute(
      'href',
      '/themes',
    )
  })
})
