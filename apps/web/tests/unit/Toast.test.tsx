import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { Toast } from '../../src/components/Toast'

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('Toast', () => {
  it('renders the message with the info kind by default', () => {
    render(<Toast message="hello" dismissLabel="Dismiss" onDismiss={() => undefined} />)
    const node = screen.getByRole('status')
    expect(node).toHaveTextContent('hello')
    expect(node).toHaveClass('toast--info')
  })

  it('applies the ok and warn variants', () => {
    const { rerender } = render(
      <Toast kind="ok" message="ok" dismissLabel="Dismiss" onDismiss={() => undefined} />,
    )
    expect(screen.getByRole('status')).toHaveClass('toast--ok')
    rerender(<Toast kind="warn" message="careful" dismissLabel="Dismiss" onDismiss={() => undefined} />)
    expect(screen.getByRole('status')).toHaveClass('toast--warn')
  })

  it('calls onDismiss after the duration elapses', () => {
    const onDismiss = vi.fn()
    render(<Toast message="x" duration={500} dismissLabel="Dismiss" onDismiss={onDismiss} />)
    expect(onDismiss).not.toHaveBeenCalled()
    act(() => {
      vi.advanceTimersByTime(500)
    })
    expect(onDismiss).toHaveBeenCalledTimes(1)
  })

  it('does not reset the timer when the parent re-renders with a new onDismiss (#355)', () => {
    const onDismiss = vi.fn()
    const { rerender } = render(
      <Toast message="x" duration={500} dismissLabel="Dismiss" onDismiss={onDismiss} />,
    )
    act(() => {
      vi.advanceTimersByTime(300)
    })
    // A parent re-render hands a brand-new inline handler identity, the way a
    // page passing `onDismiss={() => setToast(null)}` does on every keystroke.
    rerender(<Toast message="x" duration={500} dismissLabel="Dismiss" onDismiss={() => onDismiss()} />)
    act(() => {
      vi.advanceTimersByTime(200)
    })
    // 300 + 200 = 500ms total: the countdown must have survived the re-render.
    expect(onDismiss).toHaveBeenCalledTimes(1)
  })

  it('pauses the auto-dismiss timer while the pointer is over the toast', () => {
    const onDismiss = vi.fn()
    render(<Toast message="hover me" duration={500} dismissLabel="Dismiss" onDismiss={onDismiss} />)
    const node = screen.getByRole('status')

    act(() => {
      vi.advanceTimersByTime(200)
    })
    fireEvent.mouseEnter(node)
    act(() => {
      vi.advanceTimersByTime(1000)
    })
    expect(onDismiss).not.toHaveBeenCalled()

    fireEvent.mouseLeave(node)
    act(() => {
      vi.advanceTimersByTime(500)
    })
    expect(onDismiss).toHaveBeenCalledTimes(1)
  })

  it('pauses while the focusable close button has focus (#355)', () => {
    const onDismiss = vi.fn()
    render(<Toast message="focus me" duration={500} dismissLabel="Dismiss" onDismiss={onDismiss} />)
    const button = screen.getByRole('button', { name: 'Dismiss' })

    fireEvent.focus(button)
    act(() => {
      vi.advanceTimersByTime(1000)
    })
    expect(onDismiss).not.toHaveBeenCalled()

    fireEvent.blur(button)
    act(() => {
      vi.advanceTimersByTime(500)
    })
    expect(onDismiss).toHaveBeenCalledTimes(1)
  })

  it('dismisses when the close button is activated (#355)', () => {
    const onDismiss = vi.fn()
    render(<Toast message="close me" dismissLabel="Dismiss" onDismiss={onDismiss} />)
    // A keyboard user activates the button with Enter/Space, which fires click.
    fireEvent.click(screen.getByRole('button', { name: 'Dismiss' }))
    expect(onDismiss).toHaveBeenCalledTimes(1)
  })
})
