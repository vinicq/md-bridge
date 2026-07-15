import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { I18nProvider, type Locale } from '../../src/i18n'
import { convertMdToPdf } from '../../src/lib/api'
import { MdToPdf } from '../../src/pages/MdToPdf'

vi.mock('../../src/lib/api', () => ({
  convertMdToPdf: vi.fn(),
  fetchThemes: vi.fn().mockResolvedValue([
    { slug: 'default', name: 'Default', description: '', family: 'general' },
    { slug: 'academic', name: 'Academic', description: 'Serif.', family: 'serif' },
  ]),
}))

const originalCreateObjectURL = Object.getOwnPropertyDescriptor(URL, 'createObjectURL')
const originalRevokeObjectURL = Object.getOwnPropertyDescriptor(URL, 'revokeObjectURL')

function wrap(node: React.ReactNode, locale: Locale) {
  return <I18nProvider initialLocale={locale}>{node}</I18nProvider>
}

describe('MdToPdf', () => {
  beforeEach(() => {
    vi.mocked(convertMdToPdf).mockResolvedValue(new Blob(['%PDF'], { type: 'application/pdf' }))
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      value: vi.fn(() => 'blob:generated-preview'),
    })
    Object.defineProperty(URL, 'revokeObjectURL', {
      configurable: true,
      value: vi.fn(),
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
    if (originalCreateObjectURL) {
      Object.defineProperty(URL, 'createObjectURL', originalCreateObjectURL)
    } else {
      delete (URL as { createObjectURL?: unknown }).createObjectURL
    }
    if (originalRevokeObjectURL) {
      Object.defineProperty(URL, 'revokeObjectURL', originalRevokeObjectURL)
    } else {
      delete (URL as { revokeObjectURL?: unknown }).revokeObjectURL
    }
  })

  it.each([
    ['en', 'Drop a Markdown file or click to choose', 'Convert all', 'Generated PDF preview'],
    ['pt', 'Solte um arquivo Markdown ou clique para escolher', 'Converter todos', 'Pré-visualização do PDF gerado'],
    ['es', 'Suelta un archivo Markdown o haz clic para elegirlo', 'Convertir todo', 'Vista previa del PDF generado'],
  ] as const)(
    'uses the localized PDF preview iframe title for %s',
    async (locale, dropLabel, convertAllLabel, iframeTitle) => {
      const user = userEvent.setup()
      render(wrap(<MdToPdf />, locale))

      const file = new File(['# Hello'], 'sample.md', { type: 'text/markdown' })
      fireEvent.drop(screen.getByLabelText(dropLabel), {
        dataTransfer: { files: [file], items: [] as unknown as DataTransferItemList },
      })
      await screen.findByTitle('sample.md')
      await user.click(screen.getByRole('button', { name: convertAllLabel }))

      await waitFor(() => expect(convertMdToPdf).toHaveBeenCalledTimes(1), { timeout: 5000 })
      const iframe = await screen.findByTitle(iframeTitle, undefined, { timeout: 5000 })
      expect(iframe).toHaveAttribute('src', 'blob:generated-preview')
      expect(convertMdToPdf).toHaveBeenCalledTimes(1)
    },
    10000,
  )

  it('reconciles a persisted theme slug absent from the server catalog (#356)', async () => {
    // Seed a slug the mocked /themes payload ([default, academic]) does not
    // contain. Once themes load, the page must fall back to default so the
    // conversion posts a valid slug, not the stale one. Asserting the POSTED
    // theme (not the <select> value) is what proves the reconciliation: a
    // jsdom select falls back to its first option regardless.
    window.localStorage.setItem('md-bridge:md-to-pdf:theme', 'github')
    const user = userEvent.setup()
    try {
      render(wrap(<MdToPdf />, 'en'))
      // Wait until themes have loaded (the academic option proves 'ready').
      await screen.findByRole('option', { name: 'Academic' })

      const file = new File(['# Hello'], 'sample.md', { type: 'text/markdown' })
      fireEvent.drop(screen.getByLabelText('Drop a Markdown file or click to choose'), {
        dataTransfer: { files: [file], items: [] as unknown as DataTransferItemList },
      })
      await screen.findByTitle('sample.md')
      await user.click(screen.getByRole('button', { name: 'Convert all' }))

      await waitFor(() => expect(convertMdToPdf).toHaveBeenCalled(), { timeout: 5000 })
      expect(convertMdToPdf).toHaveBeenCalledWith(
        expect.any(File),
        expect.objectContaining({ theme: 'default' }),
        expect.anything(),
      )
    } finally {
      window.localStorage.removeItem('md-bridge:md-to-pdf:theme')
    }
  }, 10000)

  it('shows no success toast when the whole batch fails (#353)', async () => {
    vi.mocked(convertMdToPdf).mockRejectedValue(new Error('Failed to fetch'))
    const user = userEvent.setup()
    render(wrap(<MdToPdf />, 'en'))

    const file = new File(['# Hello'], 'sample.md', { type: 'text/markdown' })
    fireEvent.drop(screen.getByLabelText('Drop a Markdown file or click to choose'), {
      dataTransfer: { files: [file], items: [] as unknown as DataTransferItemList },
    })
    await screen.findByTitle('sample.md')
    await user.click(screen.getByRole('button', { name: 'Convert all' }))

    // The row lands in error and the success toast never appears.
    await waitFor(() => expect(convertMdToPdf).toHaveBeenCalledTimes(1), { timeout: 5000 })
    await screen.findByText('Error')
    expect(screen.queryByText('PDF ready.')).toBeNull()
  }, 10000)
})
