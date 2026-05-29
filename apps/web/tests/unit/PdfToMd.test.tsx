import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { I18nProvider } from '../../src/i18n'
import { convertPdfToMd, inspectPdf } from '../../src/lib/api'
import { PdfToMd } from '../../src/pages/PdfToMd'

vi.mock('../../src/lib/api', () => ({
  convertPdfToMd: vi.fn(),
  inspectPdf: vi.fn(),
}))

const DROP_LABEL = 'Drop a PDF file or click to choose'

function dropPdf() {
  const file = new File(['%PDF-1.4'], 'scan.pdf', { type: 'application/pdf' })
  fireEvent.drop(screen.getByLabelText(DROP_LABEL), {
    dataTransfer: { files: [file], items: [] as unknown as DataTransferItemList },
  })
}

describe('PdfToMd needs_ocr UX (#139)', () => {
  beforeEach(() => {
    vi.mocked(inspectPdf).mockResolvedValue({
      pages: 1,
      body_size_pt: 0,
      heading_sizes_pt: [],
      fonts: [],
      tagged: false,
      needs_ocr: true,
    })
  })

  afterEach(() => vi.clearAllMocks())

  it('Path B: a needs_ocr result shows a role=alert warning and a download-anyway button', async () => {
    const user = userEvent.setup()
    vi.mocked(convertPdfToMd).mockResolvedValue({
      md: '# almost empty',
      front_matter: {},
      warnings: ['needs_ocr'],
      stats: { headings: 0, tables: 0, bullets: 0 },
    } as never)

    render(
      <I18nProvider initialLocale="en">
        <PdfToMd />
      </I18nProvider>,
    )
    dropPdf()
    await screen.findByTitle('scan.pdf')
    await user.click(screen.getByRole('button', { name: 'Convert all' }))

    await waitFor(() => expect(convertPdfToMd).toHaveBeenCalledTimes(1), { timeout: 5000 })

    const alert = await screen.findByRole('alert', undefined, { timeout: 5000 })
    expect(alert).toHaveTextContent(/Warnings/i)
    // The download is reframed as an explicit escape, not the plain label.
    expect(screen.getByRole('button', { name: /Download anyway/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Download \.md$/i })).not.toBeInTheDocument()
  })

  it('Path A: a 422 ocr_required surfaces a prominent error with a how-to-enable-OCR link', async () => {
    const user = userEvent.setup()
    vi.mocked(convertPdfToMd).mockRejectedValue(
      Object.assign(new Error('OCR required'), { code: 'ocr_required' }),
    )

    render(
      <I18nProvider initialLocale="en">
        <PdfToMd />
      </I18nProvider>,
    )
    dropPdf()
    await screen.findByTitle('scan.pdf')
    await user.click(screen.getByRole('button', { name: 'Convert all' }))

    await waitFor(() => expect(convertPdfToMd).toHaveBeenCalledTimes(1), { timeout: 5000 })

    const heading = await screen.findByRole('heading', { name: /OCR required/i }, { timeout: 5000 })
    expect(heading).toBeInTheDocument()
    const cta = screen.getByRole('link', { name: /How to enable OCR/i })
    expect(cta).toHaveAttribute('href', expect.stringContaining('getting-started'))
    expect(cta).toHaveAttribute('target', '_blank')
    expect(cta).toHaveAttribute('rel', expect.stringContaining('noopener'))
  })
})
