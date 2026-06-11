import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { BatchPanel } from '../../src/components/BatchPanel'
import type { BatchItem } from '../../src/hooks/useBatchConvert'
import { I18nProvider } from '../../src/i18n'

type Result = { md: string }

function makeItem(name: string): BatchItem<Result> {
  return {
    id: name,
    file: new File(['x'], name, { type: 'application/pdf' }),
    status: 'queued',
    result: null,
    error: null,
    blobUrl: null,
  }
}

function names(container: HTMLElement): string[] {
  return Array.from(container.querySelectorAll('.batch__name')).map((node) => node.textContent ?? '')
}

function Harness({ running = false }: { running?: boolean }) {
  const [items, setItems] = useState([makeItem('a.pdf'), makeItem('b.pdf'), makeItem('c.pdf')])

  const move = (id: string, direction: -1 | 1) => {
    setItems((prev) => {
      const from = prev.findIndex((it) => it.id === id)
      const to = from + direction
      if (from === -1 || to < 0 || to >= prev.length) return prev
      const next = [...prev]
      const [item] = next.splice(from, 1)
      next.splice(to, 0, item)
      return next
    })
  }

  const moveTo = (id: string, targetId: string) => {
    setItems((prev) => {
      const from = prev.findIndex((it) => it.id === id)
      const target = prev.findIndex((it) => it.id === targetId)
      if (from === -1 || target === -1 || from === target) return prev
      const next = [...prev]
      const [item] = next.splice(from, 1)
      next.splice(target, 0, item)
      return next
    })
  }

  return (
    <I18nProvider initialLocale="en">
      <BatchPanel
        items={items}
        running={running}
        onConvertAll={() => undefined}
        onClear={() => undefined}
        onRemove={() => undefined}
        onMove={move}
        onMoveTo={moveTo}
        onDownload={() => undefined}
        downloadLabel="Download .md"
      />
    </I18nProvider>
  )
}

describe('BatchPanel reorder', () => {
  it('reorders rows through drag and drop', () => {
    const { container } = render(<Harness />)
    const dragHandle = screen.getByRole('button', { name: /drag to reorder a\.pdf/i })
    const targetRow = screen.getByTitle('b.pdf').closest('li')
    expect(targetRow).not.toBeNull()

    const data = {
      effectAllowed: '',
      dropEffect: '',
      setData: vi.fn(),
      getData: vi.fn(() => 'a.pdf'),
    }
    fireEvent.dragStart(dragHandle, { dataTransfer: data })
    fireEvent.dragOver(targetRow!, { dataTransfer: data })
    fireEvent.drop(targetRow!, { dataTransfer: data })

    expect(names(container)).toEqual(['b.pdf', 'a.pdf', 'c.pdf'])
  })

  it('reorders rows through up and down buttons', async () => {
    const user = userEvent.setup()
    const { container } = render(<Harness />)

    await user.click(screen.getByRole('button', { name: /move b\.pdf up/i }))
    expect(names(container)).toEqual(['b.pdf', 'a.pdf', 'c.pdf'])

    await user.click(screen.getByRole('button', { name: /move b\.pdf down/i }))
    expect(names(container)).toEqual(['a.pdf', 'b.pdf', 'c.pdf'])
  })

  it('reorders the focused row with keyboard shortcuts and grab mode', () => {
    const { container } = render(<Harness />)
    const rows = screen.getAllByRole('listitem')

    rows[1].focus()
    fireEvent.keyDown(rows[1], { key: 'ArrowUp', altKey: true })
    expect(names(container)).toEqual(['b.pdf', 'a.pdf', 'c.pdf'])

    const updatedRows = screen.getAllByRole('listitem')
    updatedRows[0].focus()
    fireEvent.keyDown(updatedRows[0], { key: ' ' })
    fireEvent.keyDown(updatedRows[0], { key: 'ArrowDown' })
    fireEvent.keyDown(updatedRows[0], { key: ' ' })
    expect(names(container)).toEqual(['a.pdf', 'b.pdf', 'c.pdf'])
  })

  it('disables all reorder paths while running', async () => {
    const user = userEvent.setup()
    const { container } = render(<Harness running />)
    const dragHandle = screen.getByRole('button', { name: /drag to reorder a\.pdf/i })
    const moveDown = screen.getByRole('button', { name: /move a\.pdf down/i })
    const rows = screen.getAllByRole('listitem')

    expect(dragHandle).toHaveAttribute('aria-disabled', 'true')
    expect(dragHandle).toBeDisabled()
    expect(moveDown).toBeDisabled()

    await user.click(moveDown)
    fireEvent.keyDown(rows[0], { key: 'ArrowDown', altKey: true })
    expect(names(container)).toEqual(['a.pdf', 'b.pdf', 'c.pdf'])
  })
})
