import { fireEvent, render, screen, waitFor } from '@testing-library/react'
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
  it('passes valid dropped files to onFiles', async () => {
    const onFiles = vi.fn()
    renderWithI18n(
      <DropZone accept=".pdf,application/pdf" acceptLabel="PDF" onFiles={onFiles} />,
    )
    const zone = screen.getByRole('button')
    const file = makeFile('doc.pdf', 'application/pdf')
    fireEvent.drop(zone, {
      dataTransfer: { files: [file], items: [] as unknown as DataTransferItemList },
    })
    await waitFor(() => expect(onFiles).toHaveBeenCalledTimes(1))
    expect(onFiles.mock.calls[0][0][0].name).toBe('doc.pdf')
  })

  it('shows an error when nothing matches the accept list', async () => {
    const onFiles = vi.fn()
    renderWithI18n(<DropZone accept=".pdf" acceptLabel="PDF" onFiles={onFiles} />)
    const zone = screen.getByRole('button')
    const file = makeFile('notes.txt', 'text/plain')
    fireEvent.drop(zone, {
      dataTransfer: { files: [file], items: [] as unknown as DataTransferItemList },
    })
    await waitFor(() => expect(screen.getByRole('alert').textContent).toMatch(/invalid/i))
    expect(onFiles).not.toHaveBeenCalled()
  })

  it('renders the folder hint when multiple is enabled', () => {
    renderWithI18n(
      <DropZone accept=".md" acceptLabel="Markdown" onFiles={() => undefined} multiple />,
    )
    expect(screen.getByText(/drop markdown files or a folder/i)).toBeInTheDocument()
  })

  it('renders the single-file hint when multiple is off', () => {
    renderWithI18n(<DropZone accept=".pdf" acceptLabel="PDF" onFiles={() => undefined} />)
    expect(screen.getByText(/drop a pdf/i)).toBeInTheDocument()
  })

  it('keeps the highlight over a child and clears only when leaving the zone (#359)', () => {
    renderWithI18n(<DropZone accept=".pdf" acceptLabel="PDF" onFiles={() => undefined} />)
    const zone = screen.getByRole('button')

    // Drag enters the zone.
    fireEvent.dragEnter(zone)
    expect(zone.className).toMatch(/is-over/)

    // Pointer crosses onto a child: the child's dragenter and the container's
    // dragleave both bubble here. Net depth stays > 0, so the highlight holds.
    fireEvent.dragEnter(zone)
    fireEvent.dragLeave(zone)
    expect(zone.className).toMatch(/is-over/)

    // The final dragleave takes the drag out of the zone: highlight clears.
    fireEvent.dragLeave(zone)
    expect(zone.className).not.toMatch(/is-over/)
  })

  it('is keyboard-activatable via Enter', () => {
    const onFiles = vi.fn()
    renderWithI18n(<DropZone accept=".pdf" acceptLabel="PDF" onFiles={onFiles} />)
    const zone = screen.getByRole('button')
    zone.focus()
    fireEvent.keyDown(zone, { key: 'Enter' })
    expect(onFiles).not.toHaveBeenCalled()
  })
})
