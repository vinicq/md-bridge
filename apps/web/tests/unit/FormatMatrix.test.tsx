import { act, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { FormatMatrix } from '../../src/components/FormatMatrix'
import { _resetFormatsCacheForTests } from '../../src/hooks/useFormats'
import { I18nProvider } from '../../src/i18n'
import { fetchFormats, type Format } from '../../src/lib/api'
import { hasConverterPage } from '../../src/lib/converterRoutes'

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

  it('links shipped cells that have a UI page to their converter route, from the slug', async () => {
    renderMatrix()
    const link = await screen.findByRole('link', { name: /open converter.*PDF → Markdown/i })
    expect(link).toHaveAttribute('href', '/convert/pdf-to-md')
    // Never the raw API endpoint.
    expect(link).not.toHaveAttribute('href', '/api/pdf-to-md')
  })

  it('does NOT link a shipped pair that has no UI page to a dead route', async () => {
    // md-to-docx ships in the API (#60) but has no /convert/md-to-docx page.
    renderMatrix()
    await screen.findByRole('heading', { name: /all conversions/i })
    // The pair still shows, with its Shipped pill, but it is not a navigable link.
    expect(screen.getByText('Markdown → DOCX')).toBeInTheDocument()
    expect(
      screen.queryByRole('link', { name: /Markdown → DOCX/i }),
    ).not.toBeInTheDocument()
    // And nothing anywhere points at the dead route.
    for (const link of screen.getAllByRole('link')) {
      expect(link).not.toHaveAttribute('href', '/convert/md-to-docx')
    }
  })

  it('internal converter link appears iff the slug has a UI page (integrity guard)', async () => {
    // Mirrors the backend drift guard (test_md_to_docx.py): a shipped API pair
    // only becomes a converter link when the frontend actually has its page.
    renderMatrix()
    await screen.findByRole('heading', { name: /all conversions/i })
    for (const fmt of FORMATS) {
      if (!fmt.endpoint) continue
      const internalLink = screen.queryByRole('link', {
        name: new RegExp(`open converter.*${fmt.label.replace(/[→]/g, '.')}`, 'i'),
      })
      if (hasConverterPage(fmt.slug)) {
        expect(internalLink).toHaveAttribute('href', `/convert/${fmt.slug}`)
      } else {
        expect(internalLink).toBeNull()
      }
    }
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

  it('branches on page existence, not status: a pair with an endpoint but no page is non-navigable', async () => {
    // An in-pr pair that already has a live endpoint but no SPA page must NOT
    // become a link (neither internal nor a feature request). This locks the
    // decision that the cell branches on page existence, not on status.
    const inPrNoPage: Format = {
      slug: 'epub-to-md',
      label: 'EPUB → Markdown',
      source: 'epub',
      target: 'md',
      input_mime: 'application/epub+zip',
      output_mime: 'text/markdown',
      status: 'in-pr',
      endpoint: '/api/epub-to-md',
    }
    vi.mocked(fetchFormats).mockResolvedValue([inPrNoPage])
    renderMatrix()
    await screen.findByRole('heading', { name: /all conversions/i })
    expect(screen.getByText('EPUB → Markdown')).toBeInTheDocument()
    // Has an endpoint, but no UI page: rendered static, no link at all.
    expect(screen.queryByRole('link')).toBeNull()
    // The status pill still tells the truth.
    expect(screen.getByText('In PR')).toBeInTheDocument()
  })

  it('renders nothing once the registry resolves empty (post-fetch state)', async () => {
    vi.mocked(fetchFormats).mockResolvedValueOnce([])
    const { container } = render(
      <MemoryRouter>
        <I18nProvider initialLocale="en">
          <FormatMatrix />
        </I18nProvider>
      </MemoryRouter>,
    )
    // Flush the resolved fetch so the assertion covers the ready-with-[] state,
    // not just the initial loading state (both render null, but we want the
    // post-fetch path proven).
    await act(async () => {
      await Promise.resolve()
    })
    expect(fetchFormats).toHaveBeenCalledTimes(1)
    expect(container.querySelector('.home__matrix')).toBeNull()
  })

  it('renders nothing when the registry fetch fails', async () => {
    vi.mocked(fetchFormats).mockRejectedValueOnce(new Error('registry down'))
    const { container } = render(
      <MemoryRouter>
        <I18nProvider initialLocale="en">
          <FormatMatrix />
        </I18nProvider>
      </MemoryRouter>,
    )
    await act(async () => {
      await Promise.resolve()
    })
    expect(container.querySelector('.home__matrix')).toBeNull()
  })
})
