import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Button } from '../../src/components/Button'

describe('Button', () => {
  it('renders children inside a button element', () => {
    render(<Button>Hello</Button>)
    const btn = screen.getByRole('button', { name: 'Hello' })
    expect(btn.tagName).toBe('BUTTON')
    expect(btn.getAttribute('type')).toBe('button')
  })

  it('applies the primary variant class by default', () => {
    render(<Button>x</Button>)
    expect(screen.getByRole('button')).toHaveClass('btn--primary')
  })

  it('applies the ghost variant class on demand', () => {
    render(<Button variant="ghost">x</Button>)
    expect(screen.getByRole('button')).toHaveClass('btn--ghost')
  })

  it('applies the icon variant class on demand', () => {
    render(<Button variant="icon">x</Button>)
    expect(screen.getByRole('button')).toHaveClass('btn--icon')
  })

  it('disables itself when loading and exposes aria-busy', () => {
    render(<Button loading>working</Button>)
    const btn = screen.getByRole('button')
    expect(btn).toBeDisabled()
    expect(btn).toHaveAttribute('aria-busy', 'true')
    expect(btn).toHaveClass('btn--loading')
  })

  it('forwards onClick when not loading', async () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>click</Button>)
    await userEvent.click(screen.getByRole('button'))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('does not fire onClick when disabled', async () => {
    const onClick = vi.fn()
    render(
      <Button onClick={onClick} disabled>
        disabled
      </Button>,
    )
    await userEvent.click(screen.getByRole('button'))
    expect(onClick).not.toHaveBeenCalled()
  })
})
