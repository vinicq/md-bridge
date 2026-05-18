import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { DiagnosticPanel } from '../../src/components/DiagnosticPanel'
import { I18nProvider } from '../../src/i18n'
import type { InspectPdfResponse } from '../../src/lib/api'

function wrap(node: React.ReactNode) {
  return <I18nProvider initialLocale="en">{node}</I18nProvider>
}

const SAMPLE: InspectPdfResponse = {
  pages: 4,
  body_size_pt: 11.0,
  heading_sizes_pt: [18.0, 14.0],
  fonts: [
    { name: 'BodyFont', size: 11.0, count: 100, sample: 'sample text' },
    { name: 'BoldFont', size: 18.0, count: 30, sample: 'Heading' },
  ],
  tagged: true,
  needs_ocr: false,
}

describe('DiagnosticPanel', () => {
  it('renders an empty hint when there is no data', () => {
    render(wrap(<DiagnosticPanel data={null} />))
    expect(screen.getByText(/upload a pdf to see diagnostics/i)).toBeInTheDocument()
  })

  it('renders a loading hint while inspecting', () => {
    render(wrap(<DiagnosticPanel data={null} loading />))
    expect(screen.getByText(/analyzing pdf/i)).toBeInTheDocument()
  })

  it('renders an error message when present', () => {
    render(wrap(<DiagnosticPanel data={null} error="boom" />))
    expect(screen.getByRole('alert')).toHaveTextContent('boom')
  })

  it('renders the diagnostic grid with values', () => {
    render(wrap(<DiagnosticPanel data={SAMPLE} />))
    expect(screen.getByText('Pages')).toBeInTheDocument()
    expect(screen.getByText('4')).toBeInTheDocument()
    expect(screen.getByText('11.0 pt')).toBeInTheDocument()
    expect(screen.getByText(/18\.0pt, 14\.0pt/)).toBeInTheDocument()
    expect(screen.getByText('yes')).toBeInTheDocument()
  })

  it('renders a font list inside a collapsible section', () => {
    render(wrap(<DiagnosticPanel data={SAMPLE} />))
    expect(screen.getByText(/fonts \(2\)/i)).toBeInTheDocument()
    expect(screen.getByText('BodyFont')).toBeInTheDocument()
    expect(screen.getByText('BoldFont')).toBeInTheDocument()
  })

  it('shows the OCR warning when needs_ocr is true', () => {
    const scanned = { ...SAMPLE, needs_ocr: true }
    render(wrap(<DiagnosticPanel data={scanned} />))
    expect(screen.getByText(/ocr/i)).toBeInTheDocument()
  })

  it('handles the no-heading case', () => {
    const noHeads = { ...SAMPLE, heading_sizes_pt: [] }
    render(wrap(<DiagnosticPanel data={noHeads} />))
    expect(screen.getByText('—')).toBeInTheDocument()
  })
})
