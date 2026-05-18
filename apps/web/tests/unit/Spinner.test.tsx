import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Spinner } from '../../src/components/Spinner'

describe('Spinner', () => {
  it('renders an aria-labeled status indicator', () => {
    render(<Spinner />)
    const role = screen.getByRole('status')
    expect(role).toHaveAttribute('aria-label', 'Carregando')
  })

  it('accepts a custom aria label', () => {
    render(<Spinner label="Loading data" />)
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Loading data')
  })

  it('sizes the wrapper from the size prop', () => {
    render(<Spinner size={48} />)
    const wrapper = screen.getByRole('status')
    expect(wrapper).toHaveStyle({ width: '48px', height: '48px' })
  })
})
