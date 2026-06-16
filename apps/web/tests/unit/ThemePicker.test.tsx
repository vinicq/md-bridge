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
      loadingLabel="Loading themes…"
      disabled={disabled}
    />,
  )
  return onChange
}

describe('ThemePicker', () => {
  it('renders a combobox with one option per theme', () => {
    renderPicker('default')
    const select = screen.getByRole('combobox', { name: /theme/i })
    expect(select).toBeInTheDocument()
    const options = screen.getAllByRole('option')
    expect(options).toHaveLength(THEMES.length)
    expect(screen.getByRole('option', { name: 'Academic' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Business' })).toBeInTheDocument()
  })

  it('shows the current value as selected', () => {
    renderPicker('academic')
    expect(screen.getByRole('combobox', { name: /theme/i })).toHaveValue('academic')
  })

  it('calls onChange with the slug when the user picks a theme', async () => {
    const onChange = renderPicker('default')
    await userEvent.selectOptions(
      screen.getByRole('combobox', { name: /theme/i }),
      'business',
    )
    expect(onChange).toHaveBeenCalledWith('business')
  })

  it('disables the combobox while converting', () => {
    renderPicker('default', vi.fn(), true)
    expect(screen.getByRole('combobox', { name: /theme/i })).toBeDisabled()
  })

  it('shows a loading option and disables the select when loading=true', () => {
    render(
      <ThemePicker
        themes={THEMES}
        value="default"
        onChange={vi.fn()}
        label="Theme"
        loadingLabel="Loading themes…"
        loading
      />,
    )
    expect(screen.getByRole('combobox', { name: /theme/i })).toBeDisabled()
    expect(screen.getByRole('option', { name: /loading/i })).toBeInTheDocument()
  })

  it('shows an error alert when loadError is set', () => {
    render(
      <ThemePicker
        themes={THEMES}
        value="default"
        onChange={vi.fn()}
        label="Theme"
        loadingLabel="Loading themes…"
        loadError="Could not load themes."
      />,
    )
    expect(screen.getByRole('alert')).toHaveTextContent(/could not load themes/i)
  })

  it('has an accessible label linked to the select via htmlFor/id', () => {
    renderPicker('default')
    expect(screen.getByLabelText(/theme/i)).toBeInTheDocument()
  })
})
