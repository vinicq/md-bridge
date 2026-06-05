import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { PageSetupPanel } from '../../src/components/PageSetupPanel'
import {
  DEFAULT_PAGE_SETUP,
  type PageSetupLabels,
  type PageSetupValue,
} from '../../src/components/pageSetup'

const LABELS: PageSetupLabels = {
  legend: 'Page setup',
  page: { legend: 'Page' },
  pageSize: { label: 'Page size' },
  margins: { label: 'Margins', tight: 'Tight', normal: 'Normal', loose: 'Loose' },
  header: { legend: 'Header' },
  footer: { legend: 'Footer' },
  slot: { left: 'Left', center: 'Center', right: 'Right' },
  tokenHelp: 'Use {{title}}, {{author}}, {{date}}, {{page}}, {{pages}} to insert values automatically.',
  slotPlaceholder: 'e.g. {{title}}',
}

function renderPanel(
  value: PageSetupValue = DEFAULT_PAGE_SETUP,
  onChange = vi.fn(),
  disabled = false,
) {
  render(<PageSetupPanel labels={LABELS} value={value} onChange={onChange} disabled={disabled} />)
  return onChange
}

describe('PageSetupPanel', () => {
  it('renders the nested fieldsets, two selects and six text slots', () => {
    renderPanel()
    expect(screen.getByRole('group', { name: /page setup/i })).toBeInTheDocument()
    // Page + Header + Footer child groups each carry a visible legend.
    expect(screen.getByRole('group', { name: /^page$/i })).toBeInTheDocument()
    expect(screen.getByRole('group', { name: /^header$/i })).toBeInTheDocument()
    expect(screen.getByRole('group', { name: /^footer$/i })).toBeInTheDocument()
    expect(screen.getAllByRole('combobox')).toHaveLength(2)
    expect(screen.getAllByRole('textbox')).toHaveLength(6)
  })

  it('every slot input has a visible label, never a placeholder-as-label', () => {
    renderPanel()
    // Left/Center/Right appear once per band → two each, all real <label>s.
    for (const name of [/left/i, /center/i, /right/i]) {
      expect(screen.getAllByLabelText(name)).toHaveLength(2)
    }
    // The example placeholder is illustrative, not the accessible name.
    expect(screen.getAllByPlaceholderText(/e\.g\. \{\{title\}\}/)).toHaveLength(6)
  })

  it('reflects the current values', () => {
    const value: PageSetupValue = {
      page_size: 'Letter',
      margins: 'loose',
      header: { left: 'Report', center: '', right: '{{page}}' },
      footer: { left: '', center: '{{pages}}', right: '' },
    }
    renderPanel(value)
    expect(screen.getByRole('combobox', { name: /page size/i })).toHaveValue('Letter')
    expect(screen.getByRole('combobox', { name: /margins/i })).toHaveValue('loose')
    expect(screen.getAllByLabelText(/left/i)[0]).toHaveValue('Report')
  })

  it('emits the full next value when the page size changes', async () => {
    const onChange = renderPanel()
    await userEvent.selectOptions(screen.getByRole('combobox', { name: /page size/i }), 'Legal')
    expect(onChange).toHaveBeenCalledWith({ ...DEFAULT_PAGE_SETUP, page_size: 'Legal' })
  })

  it('emits the updated band slot when a header slot is typed', async () => {
    const onChange = renderPanel()
    await userEvent.type(screen.getAllByLabelText(/center/i)[0], 'A')
    expect(onChange).toHaveBeenCalledWith({
      ...DEFAULT_PAGE_SETUP,
      header: { left: '', center: 'A', right: '' },
    })
  })

  it('shares one token-help line across all six slot inputs via aria-describedby', () => {
    renderPanel()
    const help = screen.getByText(/insert values automatically/i)
    expect(help.id).toBeTruthy()
    for (const input of screen.getAllByRole('textbox')) {
      expect(input).toHaveAttribute('aria-describedby', help.id)
    }
  })

  it('disables every control through the parent fieldset', () => {
    renderPanel(DEFAULT_PAGE_SETUP, vi.fn(), true)
    for (const control of [...screen.getAllByRole('combobox'), ...screen.getAllByRole('textbox')]) {
      expect(control).toBeDisabled()
    }
  })
})
