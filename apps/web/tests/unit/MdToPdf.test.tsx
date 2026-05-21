import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { I18nProvider, type Locale } from '../../src/i18n'
import { convertMdToPdf } from '../../src/lib/api'
import { MdToPdf } from '../../src/pages/MdToPdf'

vi.mock('../../src/lib/api', () => ({
  convertMdToPdf: vi.fn(),
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
    ['en', 'Convert', 'Generated PDF preview'],
    ['pt', 'Converter', 'Pré-visualização do PDF gerado'],
    ['es', 'Convertir', 'Vista previa del PDF generado'],
  ] as const)(
    'uses the localized PDF preview iframe title for %s',
    async (locale, convertLabel, iframeTitle) => {
      const user = userEvent.setup()
      render(wrap(<MdToPdf />, locale))

      await user.type(screen.getByRole('textbox'), '# Hello')
      await user.click(screen.getByRole('button', { name: convertLabel }))

      const iframe = await screen.findByTitle(iframeTitle)
      expect(iframe).toHaveAttribute('src', 'blob:generated-preview')
      expect(convertMdToPdf).toHaveBeenCalledTimes(1)
    },
  )
})
