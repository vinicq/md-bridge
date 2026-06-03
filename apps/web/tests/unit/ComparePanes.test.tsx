import { render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ComparePanes } from '../../src/components/ComparePanes'
import { I18nProvider } from '../../src/i18n'

function wrap(node: React.ReactNode) {
  return <I18nProvider initialLocale="en">{node}</I18nProvider>
}

// jsdom has no matchMedia; default it to the wide layout (no tabs). Individual
// tests override matches to exercise the tabbed layout.
function stubMatchMedia(matches: boolean) {
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockReturnValue({
      matches,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }),
  )
}

afterEach(() => vi.unstubAllGlobals())

describe('ComparePanes', () => {
  describe('wide layout (no tabs)', () => {
    beforeEach(() => stubMatchMedia(false))

    it('renders the source iframe with a file-named accessible title', () => {
      render(wrap(<ComparePanes pdfUrl="blob:abc" pdfName="report.pdf" markdown="# Hi" />))
      const frame = screen.getByTitle('Source PDF: report.pdf')
      expect(frame).toHaveAttribute('src', 'blob:abc')
      // No tablist in the wide layout.
      expect(screen.queryByRole('tablist')).not.toBeInTheDocument()
    })

    it('shows the empty placeholder when no PDF is selected (no iframe)', () => {
      render(wrap(<ComparePanes pdfUrl={null} pdfName={null} markdown="" />))
      expect(screen.getByText(/drop a pdf to preview/i)).toBeInTheDocument()
      expect(screen.queryByTitle(/source pdf/i)).not.toBeInTheDocument()
    })

    it('shows the source error placeholder instead of a misleading scan render', () => {
      render(
        wrap(<ComparePanes pdfUrl="blob:abc" pdfName="scan.pdf" markdown="" sourceError />),
      )
      expect(screen.getByText(/no text layer to convert/i)).toBeInTheDocument()
      expect(screen.queryByTitle(/source pdf/i)).not.toBeInTheDocument()
    })

    it('renders the converted Markdown in the result pane', () => {
      render(wrap(<ComparePanes pdfUrl="blob:abc" pdfName="r.pdf" markdown="# Heading X" />))
      expect(screen.getByRole('heading', { name: 'Heading X' })).toBeInTheDocument()
    })
  })

  describe('tabbed layout (<= 768px)', () => {
    beforeEach(() => stubMatchMedia(true))

    it('renders a tablist defaulting to the Markdown tab', () => {
      render(wrap(<ComparePanes pdfUrl="blob:abc" pdfName="r.pdf" markdown="# Hi" />))
      expect(screen.getByRole('tablist')).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: 'Markdown' })).toHaveAttribute('aria-selected', 'true')
      expect(screen.getByRole('tab', { name: 'PDF' })).toHaveAttribute('aria-selected', 'false')
    })

    it('keeps both panes mounted, hiding the inactive one', () => {
      render(wrap(<ComparePanes pdfUrl="blob:abc" pdfName="r.pdf" markdown="# Hi" />))
      // PDF panel is mounted but hidden by default (MD is active).
      const pdfPanel = document.getElementById('compare-panel-pdf')
      const mdPanel = document.getElementById('compare-panel-md')
      expect(pdfPanel).toHaveAttribute('hidden')
      expect(mdPanel).not.toHaveAttribute('hidden')
    })
  })
})
