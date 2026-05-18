import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { DropZone } from '../../src/components/DropZone'
import { I18nProvider } from '../../src/i18n'

function makeFile(name: string, type: string, size = 100) {
  return new File([new Uint8Array(size)], name, { type })
}

function renderWithI18n(ui: React.ReactNode) {
  return render(<I18nProvider initialLocale="en">{ui}</I18nProvider>)
}

describe('DropZone', () => {
  it('triggers onFile when a matching file is dropped', () => {
    const onFile = vi.fn()
    renderWithI18n(<DropZone accept=".pdf,application/pdf" acceptLabel="PDF" onFile={onFile} />)
    const zone = screen.getByRole('button')
    const file = makeFile('doc.pdf', 'application/pdf')
    fireEvent.drop(zone, { dataTransfer: { files: [file] } })
    expect(onFile).toHaveBeenCalledTimes(1)
    expect(onFile.mock.calls[0][0].name).toBe('doc.pdf')
  })

  it('shows an error for an invalid mime', () => {
    const onFile = vi.fn()
    renderWithI18n(<DropZone accept=".pdf" acceptLabel="PDF" onFile={onFile} />)
    const zone = screen.getByRole('button')
    const file = makeFile('notes.txt', 'text/plain')
    fireEvent.drop(zone, { dataTransfer: { files: [file] } })
    expect(onFile).not.toHaveBeenCalled()
    expect(screen.getByRole('alert').textContent).toMatch(/invalid/i)
  })

  it('renders the file name when one is set', () => {
    renderWithI18n(
      <DropZone
        accept=".pdf"
        acceptLabel="PDF"
        onFile={() => undefined}
        file={makeFile('report.pdf', 'application/pdf', 2048)}
      />,
    )
    expect(screen.getByText('report.pdf')).toBeInTheDocument()
    expect(screen.getByText(/KB/)).toBeInTheDocument()
  })

  it('is keyboard-activatable via Enter', () => {
    const onFile = vi.fn()
    renderWithI18n(<DropZone accept=".pdf" acceptLabel="PDF" onFile={onFile} />)
    const zone = screen.getByRole('button')
    zone.focus()
    fireEvent.keyDown(zone, { key: 'Enter' })
    expect(onFile).not.toHaveBeenCalled()
  })
})
