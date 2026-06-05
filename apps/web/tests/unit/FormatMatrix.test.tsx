import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { FormatMatrix } from '../../src/components/FormatMatrix'
import { _resetFormatsCacheForTests } from '../../src/hooks/useFormats'
import { I18nProvider } from '../../src/i18n'
import { fetchFormats, type Format } from '../../src/lib/api'

vi.mock('../../src/lib/api', () => ({ fetchFormats: vi.fn() }))

// A fixture covering both link paths (shipped endpoint vs planned null) and all
// four status variants, so the pill mapping and the routing are both exercised.
const FORMATS: Format[] = [
  { slug: 'pdf-to-md', label: 'PDF → Markdown', source: 'pdf', target: 'md', input_mime: 'application/pdf', output_mime: 'text/markdown', status: 'shipped', endpoint: '/api/pdf-to-md' },
  { slug: 'md-to-docx', label: 'Markdown → DOCX', source: 'md', target: 'docx', input_mime: 'text/markdown', output_mime: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', status: 'shipped', endpoint: '/api/md-to-docx' },
  { slug: 'rtf-to-md', label: 'RTF → Markdown', source: 'rtf', target: 'md', input_mime: 'application/rtf', output_mime: 'text/markdown', status: 'in-pr', endpoint: null },
  { slug: 'md-to-html', label: 'Markdown → HTML', source: 'md', target: 'html', input_mime: 'text/markdown', output_mime: 'text/html', status: 'roadmap', endpoint: null },
  { slug: 'docx-to-md', label: 'DOCX → Markdown', source: 'docx', target: 'md', input_mime: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', output_mime: 'text/markdown', status: 'wanted', endpoint: null },
]

function renderMatrix() {
  render(
    <MemoryRouter>
      <I18nProvider initialLocale="en">
        <FormatMatrix />
      </I18nProvider>
    </MemoryRouter>,
  )
}

describe('FormatMatrix', () => {
  beforeEach(() => {
    _resetFormatsCacheForTests()
    vi.mocked(fetchFormats).mockResolvedValue(FORMATS)
  })

  afterEach(() => {
    vi.clearAllMocks()
    _resetFormatsCacheForTests()
  })

  it('renders one cell per pair from the registry payload, no hard-coded list', async () => {
    renderMatrix()
    expect(await screen.findByRole('heading', { name: /all conversions/i })).toBeInTheDocument()
    expect(screen.getAllByRole('listitem')).toHaveLength(FORMATS.length)
    // Labels come from the API verbatim.
    expect(screen.getByText('Markdown → DOCX')).toBeInTheDocument()
  })

  it('links shipped cells to their converter route, derived from the slug', async () => {
    renderMatrix()
    const link = await screen.findByRole('link', { name: /open converter.*Markdown → DOCX/i })
    expect(link).toHaveAttribute('href', '/convert/md-to-docx')
    // Never the raw API endpoint.
    expect(link).not.toHaveAttribute('href', '/api/md-to-docx')
  })

  it('links planned cells to a prefilled feature request that opens in a new tab', async () => {
    renderMatrix()
    const link = await screen.findByRole('link', {
      name: /request this pair.*Markdown → HTML.*opens in a new tab/i,
    })
    const href = link.getAttribute('href') ?? ''
    expect(href).toContain('/issues/new')
    expect(href).toContain('template=feature_request.md')
    expect(href).toContain('title=feature%3A+md-to-html')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', expect.stringContaining('noopener'))
  })

  it('shows the right status pill text per cell, status as text not color alone', async () => {
    renderMatrix()
    await screen.findByRole('heading', { name: /all conversions/i })
    expect(screen.getAllByText('Shipped')).toHaveLength(2)
    expect(screen.getByText('In PR')).toBeInTheDocument()
    expect(screen.getByText('Roadmap')).toBeInTheDocument()
    expect(screen.getByText('Wanted')).toBeInTheDocument()
  })

  it('every cell link carries a unique, self-describing accessible name', async () => {
    renderMatrix()
    await screen.findByRole('heading', { name: /all conversions/i })
    const names = screen.getAllByRole('link').map((a) => a.getAttribute('aria-label') ?? a.textContent)
    expect(new Set(names).size).toBe(names.length)
  })

  it('renders nothing when the registry is empty or the fetch fails', async () => {
    vi.mocked(fetchFormats).mockResolvedValue([])
    const { container } = render(
      <MemoryRouter>
        <I18nProvider initialLocale="en">
          <FormatMatrix />
        </I18nProvider>
      </MemoryRouter>,
    )
    // Give the effect a tick to resolve, then assert no matrix rendered.
    await Promise.resolve()
    expect(container.querySelector('.home__matrix')).toBeNull()
  })
})
