import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { PresetChips } from '../../src/components/PresetChips'
import type { Preset } from '../../src/lib/presets'
import { I18nProvider } from '../../src/i18n'

function preset(over: Partial<Preset> = {}): Preset {
  return {
    id: over.id ?? 'id-1',
    name: over.name ?? 'Briefs',
    pair: 'md-to-pdf',
    options: { theme: 'academic' },
    createdAt: Date.now(),
    ...over,
  }
}

function renderChips(props: Partial<React.ComponentProps<typeof PresetChips>> = {}) {
  const handlers = {
    presets: [preset()],
    activeId: null as string | null,
    atCap: false,
    onApply: vi.fn(),
    onDelete: vi.fn(),
    onSave: vi.fn(),
    onImport: vi.fn(),
    onExport: vi.fn(),
  }
  const merged = { ...handlers, ...props }
  render(
    <I18nProvider initialLocale="en">
      <PresetChips {...merged} />
    </I18nProvider>,
  )
  return merged
}

describe('PresetChips (#62)', () => {
  it('shows the empty message with no presets', () => {
    renderChips({ presets: [] })
    expect(screen.getByText(/No presets yet/i)).toBeTruthy()
  })

  it('applies a preset when its chip is clicked', () => {
    const onApply = vi.fn()
    renderChips({ presets: [preset({ id: 'a', name: 'Briefs' })], onApply })
    fireEvent.click(screen.getByRole('button', { name: /Apply preset Briefs/i }))
    expect(onApply).toHaveBeenCalledTimes(1)
    expect(onApply.mock.calls[0][0].id).toBe('a')
  })

  it('marks the active preset with aria-current and deletes via a labelled button', () => {
    const onDelete = vi.fn()
    renderChips({ presets: [preset({ id: 'a', name: 'Briefs' })], activeId: 'a', onDelete })
    expect(
      screen.getByRole('button', { name: /Apply preset Briefs/i }).getAttribute('aria-current'),
    ).toBe('true')
    fireEvent.click(screen.getByRole('button', { name: /Delete preset Briefs/i }))
    expect(onDelete).toHaveBeenCalledWith('a')
  })

  it('disables the add chip and shows a status warning at the cap', () => {
    renderChips({ atCap: true })
    expect(screen.getByRole('button', { name: 'Save current' }).hasAttribute('disabled')).toBe(true)
    expect(screen.getByRole('status')).toBeTruthy()
    expect(screen.getByText(/Preset limit reached/i)).toBeTruthy()
  })

  it('names and saves a new preset', () => {
    const onSave = vi.fn()
    renderChips({ presets: [], onSave })
    fireEvent.click(screen.getByRole('button', { name: 'Save current' }))
    const input = screen.getByRole('textbox', { name: /Preset name/i })
    fireEvent.change(input, { target: { value: 'Reports' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(onSave).toHaveBeenCalledWith('Reports')
  })

  it('fires import and export', () => {
    const onExport = vi.fn()
    renderChips({ presets: [preset()], onExport })
    fireEvent.click(screen.getByRole('button', { name: 'Export JSON' }))
    expect(onExport).toHaveBeenCalledTimes(1)
    // The Import button is present (the file input itself is hidden).
    expect(screen.getByRole('button', { name: 'Import' })).toBeTruthy()
  })
})
