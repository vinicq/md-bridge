import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Spinner } from '../../src/components/Spinner'

describe('Spinner', () => {
  it('renders a status indicator with the required aria label', () => {
    render(<Spinner label="Loading data" />)
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Loading data')
  })

  it('sizes the wrapper from the size prop', () => {
    render(<Spinner size={48} label="Loading data" />)
    const wrapper = screen.getByRole('status')
    expect(wrapper).toHaveStyle({ width: '48px', height: '48px' })
  })
})
