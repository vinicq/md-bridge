import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { I18nProvider } from '../../src/i18n'
import { fetchThemeCss, fetchThemes } from '../../src/lib/api'
import { _resetThemesCacheForTests } from '../../src/hooks/useThemes'
import { Themes } from '../../src/pages/Themes'

// #392: the theme library renders the API catalog, filters by family, badges the
// pack themes, and shows a read-only theme CSS tab. The iframe preview is not
// asserted here (it renders in a real browser; jsdom stops at the shell).

vi.mock('../../src/lib/api', () => ({
  fetchThemes: vi.fn(),
  fetchThemeCss: vi.fn(),
}))

const THEMES = [
  { slug: 'default', name: 'Default', description: '', family: 'general' },
  { slug: 'academic', name: 'Academic', description: '', family: 'serif' },
  { slug: 'business', name: 'Business', description: '', family: 'sans' },
  { slug: 'notebook', name: 'Notebook', description: '', family: 'monospace' },
]

function renderPage() {
  return render(
    <I18nProvider initialLocale="en">
      <MemoryRouter>
        <Themes />
      </MemoryRouter>
    </I18nProvider>,
  )
}

beforeEach(() => {
  _resetThemesCacheForTests()
  vi.mocked(fetchThemes).mockResolvedValue(THEMES as never)
  vi.mocked(fetchThemeCss).mockResolvedValue('body{color:red}')
})

afterEach(() => vi.clearAllMocks())

describe('Theme library (#392)', () => {
  it('renders a tile for every theme from the API', async () => {
    renderPage()
    expect(await screen.findByRole('button', { name: /Academic/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Business/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Notebook/ })).toBeInTheDocument()
  })

  it('badges a pack theme as NEW and leaves originals unbadged', async () => {
    renderPage()
    await screen.findByRole('button', { name: /Notebook/ })
    // Only notebook (pack) is badged among these four.
    expect(screen.getAllByText('NEW')).toHaveLength(1)
  })

  it('filters by family: Sans hides serif themes', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByRole('button', { name: /Academic/ })
    await user.click(screen.getByRole('button', { name: 'Sans' }))
    expect(screen.queryByRole('button', { name: /Academic/ })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Business/ })).toBeInTheDocument()
  })

  it('shows the theme CSS on the read-only source tab', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByRole('button', { name: /Academic/ })
    await user.click(screen.getByRole('tab', { name: /Theme CSS/ }))
    expect(await screen.findByLabelText('Theme CSS')).toHaveTextContent('body{color:red}')
  })
})
