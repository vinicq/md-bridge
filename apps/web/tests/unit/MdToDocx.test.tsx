import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { I18nProvider, type Locale } from '../../src/i18n'
import { convertMdToDocx } from '../../src/lib/api'
import { MdToDocx } from '../../src/pages/MdToDocx'

vi.mock('../../src/lib/api', () => ({
  convertMdToDocx: vi.fn(),
}))

const DOCX_MIME = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

const originalCreateObjectURL = Object.getOwnPropertyDescriptor(URL, 'createObjectURL')
const originalRevokeObjectURL = Object.getOwnPropertyDescriptor(URL, 'revokeObjectURL')

function wrap(node: React.ReactNode, locale: Locale) {
  return <I18nProvider initialLocale={locale}>{node}</I18nProvider>
}

describe('MdToDocx', () => {
  beforeEach(() => {
    vi.mocked(convertMdToDocx).mockResolvedValue(new Blob(['PK\x03\x04'], { type: DOCX_MIME }))
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      value: vi.fn(() => 'blob:generated-docx'),
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
    ['en', 'Markdown to DOCX', 'Drop a Markdown file or click to choose', 'Convert all', 'Download .docx'],
    ['pt', 'Markdown para DOCX', 'Solte um arquivo Markdown ou clique para escolher', 'Converter todos', 'Baixar .docx'],
    ['es', 'Markdown a DOCX', 'Suelta un archivo Markdown o haz clic para elegirlo', 'Convertir todo', 'Descargar .docx'],
  ] as const)(
    'converts via convertMdToDocx and surfaces the localized download for %s',
    async (locale, title, dropLabel, convertAllLabel, downloadLabel) => {
      const user = userEvent.setup()
      render(wrap(<MdToDocx />, locale))

      expect(screen.getByRole('heading', { name: title })).toBeInTheDocument()

      const file = new File(['# Hello'], 'sample.md', { type: 'text/markdown' })
      fireEvent.drop(screen.getByLabelText(dropLabel), {
        dataTransfer: { files: [file], items: [] as unknown as DataTransferItemList },
      })
      await screen.findByText('sample.md')
      await user.click(screen.getByRole('button', { name: convertAllLabel }))

      await waitFor(() => expect(convertMdToDocx).toHaveBeenCalledTimes(1), { timeout: 5000 })
      // The localized download affordance carries the .docx extension so the
      // user knows the output format (top action bar + per-item row both use it).
      await waitFor(() =>
        expect(screen.getAllByRole('button', { name: downloadLabel }).length).toBeGreaterThan(0),
      )
      // No result iframe: a .docx cannot render in-browser. The right pane stays
      // a markdown preview of the input.
      expect(document.querySelector('iframe')).toBeNull()
    },
    10000,
  )
})
