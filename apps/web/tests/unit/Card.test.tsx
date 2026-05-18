import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Card } from '../../src/components/Card'

describe('Card', () => {
  it('renders children and the surface variant by default', () => {
    render(<Card>content</Card>)
    const div = screen.getByText('content').closest('.card')
    expect(div).not.toBeNull()
    expect(div).toHaveClass('card--surface')
  })

  it('applies the outline variant on demand', () => {
    render(<Card variant="outline">content</Card>)
    const div = screen.getByText('content').closest('.card')
    expect(div).toHaveClass('card--outline')
  })

  it('forwards additional className and html attributes', () => {
    render(
      <Card className="custom" data-testid="card-id">
        x
      </Card>,
    )
    const card = screen.getByTestId('card-id')
    expect(card).toHaveClass('card', 'card--surface', 'custom')
  })
})
