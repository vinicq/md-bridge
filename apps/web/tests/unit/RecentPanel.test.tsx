import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { RecentPanel } from '../../src/components/RecentPanel'
import type { HistoryEntry } from '../../src/lib/history'
import { I18nProvider } from '../../src/i18n'

function entry(over: Partial<HistoryEntry> = {}): HistoryEntry {
  return {
    id: 'id-1',
    name: 'file.pdf',
    pair: 'pdf-to-md',
    size: 2_400_000,
    options: {},
    outcome: 'done',
    createdAt: Date.now(),
    ...over,
  }
}

function renderPanel(
  props: Partial<React.ComponentProps<typeof RecentPanel>> = {},
) {
  const handlers = {
    isLive: () => true,
    onRedownload: vi.fn(),
    onRerun: vi.fn(),
    onClear: vi.fn(),
  }
  const utils = render(
    <I18nProvider initialLocale="en">
      <RecentPanel entries={[entry()]} {...handlers} {...props} />
    </I18nProvider>,
  )
  return { ...utils, ...handlers, ...props }
}

describe('RecentPanel (#63)', () => {
  it('shows the empty message when there are no entries', () => {
    renderPanel({ entries: [] })
    expect(screen.getByText('No recent conversions yet.')).toBeTruthy()
    // No Clear all when empty.
    expect(screen.queryByText('Clear all')).toBeNull()
  })

  it('renders the entry name and human-readable size', () => {
    renderPanel({ entries: [entry({ name: 'report.pdf' })] })
    expect(screen.getByText('report.pdf')).toBeTruthy()
    expect(screen.getByText(/2\.29 MB/)).toBeTruthy()
  })

  it('offers Re-download only while the result is live, and re-runs it back', () => {
    const onRedownload = vi.fn()
    renderPanel({ isLive: () => true, onRedownload })
    const btn = screen.getByRole('button', { name: /Re-download the result of/ })
    fireEvent.click(btn)
    expect(onRedownload).toHaveBeenCalledTimes(1)
  })

  it('hides Re-download when the result is not live (expired), keeping Re-run', () => {
    renderPanel({ isLive: () => false })
    expect(screen.queryByRole('button', { name: /Re-download the result of/ })).toBeNull()
    expect(screen.getByRole('button', { name: /Re-run the conversion of/ })).toBeTruthy()
  })

  it('marks a needs_ocr row as warn and never offers Re-download, even live', () => {
    const { container } = renderPanel({
      isLive: () => true,
      entries: [entry({ outcome: 'needs_ocr' })],
    })
    expect(container.querySelector('.recent-row--warn')).toBeTruthy()
    // needs_ocr produced no usable Markdown, so no Re-download regardless of live.
    expect(screen.queryByRole('button', { name: /Re-download the result of/ })).toBeNull()
    expect(screen.getByRole('button', { name: /Re-run the conversion of/ })).toBeTruthy()
  })

  it('disables Re-run while a batch is busy so it cannot silently queue', () => {
    const onRerun = vi.fn()
    renderPanel({ busy: true, onRerun })
    const rerun = screen.getByRole('button', { name: /Re-run the conversion of/ })
    expect(rerun.hasAttribute('disabled')).toBe(true)
    fireEvent.click(rerun)
    expect(onRerun).not.toHaveBeenCalled()
  })

  it('fires the row handlers', () => {
    const onRerun = vi.fn()
    const onClear = vi.fn()
    renderPanel({ onRerun, onClear })
    fireEvent.click(screen.getByRole('button', { name: /Re-run the conversion of/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Clear all' }))
    expect(onRerun).toHaveBeenCalledTimes(1)
    expect(onClear).toHaveBeenCalledTimes(1)
  })
})
