import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Switch } from '../../src/components/Switch'

describe('Switch', () => {
  it('renders as a switch with the accessible name and off state', () => {
    render(<Switch checked={false} onChange={() => {}} label="Feature" onText="On" offText="Off" />)
    const sw = screen.getByRole('switch', { name: 'Feature' })
    expect(sw).toHaveAttribute('aria-checked', 'false')
    expect(sw).toHaveTextContent('Off')
  })

  it('reflects the checked prop', () => {
    render(<Switch checked onChange={() => {}} label="Feature" onText="On" offText="Off" />)
    const sw = screen.getByRole('switch')
    expect(sw).toHaveAttribute('aria-checked', 'true')
    expect(sw).toHaveTextContent('On')
  })

  it('fires onChange with the toggled value', async () => {
    const onChange = vi.fn()
    render(<Switch checked={false} onChange={onChange} label="Feature" onText="On" offText="Off" />)
    await userEvent.click(screen.getByRole('switch'))
    expect(onChange).toHaveBeenCalledWith(true)
  })

  it('links the hint via aria-describedby', () => {
    render(
      <Switch
        checked={false}
        onChange={() => {}}
        label="Feature"
        onText="On"
        offText="Off"
        describedBy="hint-x"
      />,
    )
    expect(screen.getByRole('switch')).toHaveAttribute('aria-describedby', 'hint-x')
  })

  it('does not fire onChange when disabled', async () => {
    const onChange = vi.fn()
    render(
      <Switch checked={false} onChange={onChange} label="Feature" onText="On" offText="Off" disabled />,
    )
    await userEvent.click(screen.getByRole('switch'))
    expect(onChange).not.toHaveBeenCalled()
  })
})
