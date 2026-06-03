import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { OptionsPanel, type OptionField } from '../../src/components/OptionsPanel'

const FIELDS: OptionField[] = [
  { id: 'front_matter', kind: 'toggle', label: 'Add front matter', tooltip: 'Title, author, date.' },
  { id: 'page_break', kind: 'toggle', label: 'Mark page breaks' },
  {
    id: 'max_heading_level',
    kind: 'select',
    label: 'Deepest heading level',
    disabled: true,
    options: [1, 2, 3].map((n) => ({ value: String(n), label: String(n) })),
  },
]

function renderPanel(values: Record<string, boolean | string | number>, onChange = vi.fn(), disabled = false) {
  render(
    <OptionsPanel
      legend="Conversion options"
      fields={FIELDS}
      values={values}
      onChange={onChange}
      disabled={disabled}
    />,
  )
  return onChange
}

describe('OptionsPanel', () => {
  it('renders the legend and one control per field', () => {
    renderPanel({ front_matter: true, page_break: false, max_heading_level: '3' })
    expect(screen.getByRole('group', { name: /conversion options/i })).toBeInTheDocument()
    expect(screen.getAllByRole('checkbox')).toHaveLength(2)
    expect(screen.getByRole('combobox', { name: /deepest heading level/i })).toBeInTheDocument()
  })

  it('reflects the current values', () => {
    renderPanel({ front_matter: true, page_break: false, max_heading_level: '2' })
    expect(screen.getByRole('checkbox', { name: /add front matter/i })).toBeChecked()
    expect(screen.getByRole('checkbox', { name: /mark page breaks/i })).not.toBeChecked()
    expect(screen.getByRole('combobox', { name: /deepest heading level/i })).toHaveValue('2')
  })

  it('emits the field id and new value on toggle', async () => {
    const onChange = renderPanel({ front_matter: true, page_break: false, max_heading_level: '3' })
    await userEvent.click(screen.getByRole('checkbox', { name: /mark page breaks/i }))
    expect(onChange).toHaveBeenCalledWith('page_break', true)
  })

  it('exposes a tooltip via the native title attribute', () => {
    renderPanel({ front_matter: true, page_break: false, max_heading_level: '3' })
    const row = screen.getByRole('checkbox', { name: /add front matter/i }).closest('.options-panel__row')
    expect(row).toHaveAttribute('title', 'Title, author, date.')
  })

  it('disables a field flagged disabled (e.g. dependent control)', () => {
    renderPanel({ front_matter: true, page_break: false, max_heading_level: '3' })
    expect(screen.getByRole('combobox', { name: /deepest heading level/i })).toBeDisabled()
  })

  it('locks the whole panel while converting', async () => {
    const onChange = renderPanel({ front_matter: true, page_break: false, max_heading_level: '3' }, vi.fn(), true)
    const toggle = screen.getByRole('checkbox', { name: /mark page breaks/i })
    expect(toggle).toBeDisabled()
    await userEvent.click(toggle)
    expect(onChange).not.toHaveBeenCalled()
  })
})
