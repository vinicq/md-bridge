import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { I18nProvider, type Locale } from '../../src/i18n'
import { convertMdToPdf, fetchThemes } from '../../src/lib/api'
import { _resetThemesCacheForTests } from '../../src/hooks/useThemes'
import { MdToPdf } from '../../src/pages/MdToPdf'

vi.mock('../../src/lib/api', () => ({
  convertMdToPdf: vi.fn(),
  fetchThemeCss: vi.fn().mockResolvedValue('body{}'),
  fetchThemes: vi.fn().mockResolvedValue([
    { slug: 'default', name: 'Default', description: '', family: 'general' },
    { slug: 'academic', name: 'Academic', description: 'Serif.', family: 'serif' },
  ]),
}))

const originalCreateObjectURL = Object.getOwnPropertyDescriptor(URL, 'createObjectURL')
const originalRevokeObjectURL = Object.getOwnPropertyDescriptor(URL, 'revokeObjectURL')

function wrap(node: React.ReactNode, locale: Locale) {
  return (
    <I18nProvider initialLocale={locale}>
      <MemoryRouter>{node}</MemoryRouter>
    </I18nProvider>
  )
}

describe('MdToPdf', () => {
  beforeEach(() => {
    // The MD→PDF theme now lives in the unified prefs key (#64), migrated once
    // from the legacy key. Clear storage so each test's seeded legacy value
    // actually migrates instead of being shadowed by a prior test's prefs blob.
    window.localStorage.clear()
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

  it('re-runs a stale-slug batch with default once the catalog loads (#356 race)', async () => {
    // If /api/themes resolves after a conversion already ran with a stale slug,
    // activeTheme flips to default without `theme` changing. Keying the re-run
    // effect on activeTheme heals the batch: it re-converts with the valid theme.
    _resetThemesCacheForTests()
    let resolveThemes!: (v: unknown) => void
    vi.mocked(fetchThemes).mockReturnValueOnce(
      new Promise((res) => {
        resolveThemes = res
      }) as ReturnType<typeof fetchThemes>,
    )
    window.localStorage.setItem('md-bridge:md-to-pdf:theme', 'github')
    const user = userEvent.setup()
    try {
      render(wrap(<MdToPdf />, 'en'))
      // Catalog still loading: activeTheme is the stale 'github'.
      const file = new File(['# Hello'], 'sample.md', { type: 'text/markdown' })
      fireEvent.drop(screen.getByLabelText('Drop a Markdown file or click to choose'), {
        dataTransfer: { files: [file], items: [] as unknown as DataTransferItemList },
      })
      await screen.findByTitle('sample.md')
      await user.click(screen.getByRole('button', { name: 'Convert all' }))
      await waitFor(() => expect(convertMdToPdf).toHaveBeenCalled(), { timeout: 5000 })
      expect(vi.mocked(convertMdToPdf).mock.calls[0][1]).toMatchObject({ theme: 'github' })

      // Catalog resolves without 'github': activeTheme -> default -> batch re-runs.
      await act(async () => {
        resolveThemes([
          { slug: 'default', name: 'Default', description: '', family: 'general' },
          { slug: 'academic', name: 'Academic', description: '', family: 'serif' },
        ])
      })
      await waitFor(
        () => {
          const themes = vi
            .mocked(convertMdToPdf)
            .mock.calls.map((c) => (c[1] as { theme?: string }).theme)
          expect(themes).toContain('default')
        },
        { timeout: 5000 },
      )
    } finally {
      window.localStorage.removeItem('md-bridge:md-to-pdf:theme')
      _resetThemesCacheForTests()
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

  it('previews pasted markdown with the selected theme before conversion (#397)', async () => {
    render(wrap(<MdToPdf />, 'en'))
    fireEvent.change(screen.getByLabelText('Pasted markdown'), {
      target: { value: '# Hello\n\nBody.' },
    })
    // The themed live preview iframe appears, no backend round-trip needed.
    expect(await screen.findByTitle('Live theme preview')).toBeInTheDocument()
  })

  it('sends the user custom CSS with the conversion (#395)', async () => {
    const user = userEvent.setup()
    render(wrap(<MdToPdf />, 'en'))
    fireEvent.change(screen.getByLabelText('Pasted markdown'), { target: { value: '# Hi' } })
    fireEvent.change(screen.getByLabelText('Custom CSS'), {
      target: { value: 'body { color: red }' },
    })
    await user.click(screen.getByRole('button', { name: 'Convert' }))
    await waitFor(() => expect(convertMdToPdf).toHaveBeenCalled(), { timeout: 5000 })
    expect(vi.mocked(convertMdToPdf).mock.calls[0][1]).toMatchObject({
      custom_css: 'body { color: red }',
    })
  })

  it('saves the current theme as a preset and re-applies it on the conversion (#62)', async () => {
    const user = userEvent.setup()
    render(wrap(<MdToPdf />, 'en'))
    await screen.findByRole('option', { name: 'Academic' })
    const select = screen.getByRole('combobox')
    await user.selectOptions(select, 'academic')

    // Save the current setup (theme=academic) as a named preset.
    await user.click(screen.getByRole('button', { name: 'Save current' }))
    fireEvent.change(screen.getByRole('textbox', { name: /Preset name/i }), {
      target: { value: 'Briefs' },
    })
    await user.click(screen.getByRole('button', { name: 'Save' }))
    expect(screen.getByRole('button', { name: /Apply preset Briefs/i })).toBeInTheDocument()

    // Switch away, then apply the preset to restore academic.
    await user.selectOptions(select, 'default')
    await user.click(screen.getByRole('button', { name: /Apply preset Briefs/i }))

    // The conversion posts the preset's theme, proving apply re-wired the form.
    fireEvent.change(screen.getByLabelText('Pasted markdown'), { target: { value: '# Hi' } })
    await user.click(screen.getByRole('button', { name: 'Convert' }))
    await waitFor(() => expect(convertMdToPdf).toHaveBeenCalled(), { timeout: 5000 })
    expect(vi.mocked(convertMdToPdf).mock.calls.at(-1)![1]).toMatchObject({ theme: 'academic' })
  }, 10000)

  it('sends render_mermaid per the toggle and re-runs when it flips (#439)', async () => {
    const user = userEvent.setup()
    render(wrap(<MdToPdf />, 'en'))

    // Default off: the conversion posts render_mermaid: false.
    fireEvent.change(screen.getByLabelText('Pasted markdown'), { target: { value: '# Hi' } })
    await user.click(screen.getByRole('button', { name: 'Convert' }))
    await waitFor(() => expect(convertMdToPdf).toHaveBeenCalled(), { timeout: 5000 })
    expect(vi.mocked(convertMdToPdf).mock.calls.at(-1)![1]).toMatchObject({ render_mermaid: false })

    // Turning the switch on re-runs the queue with render_mermaid: true.
    await user.click(screen.getByRole('switch', { name: /render mermaid/i }))
    await waitFor(
      () =>
        expect(vi.mocked(convertMdToPdf).mock.calls.at(-1)![1]).toMatchObject({
          render_mermaid: true,
        }),
      { timeout: 5000 },
    )
  }, 10000)

  it('does not auto-convert a purely-queued batch when an option toggles (#464)', async () => {
    // Files dropped but never converted stay queued: toggling an option must not
    // silently start the upload/conversion. The re-run effect only refreshes a
    // batch that already produced a result; a queued-only batch waits for Convert.
    const user = userEvent.setup()
    render(wrap(<MdToPdf />, 'en'))

    const file = new File(['# Hi'], 'sample.md', { type: 'text/markdown' })
    fireEvent.drop(screen.getByLabelText('Drop a Markdown file or click to choose'), {
      dataTransfer: { files: [file], items: [] as unknown as DataTransferItemList },
    })
    await screen.findByTitle('sample.md')

    await user.click(screen.getByRole('switch', { name: /render mermaid/i }))
    // Give the effect a tick to settle; a queued-only batch must not convert.
    await new Promise((r) => setTimeout(r, 50))
    expect(convertMdToPdf).not.toHaveBeenCalled()
  }, 10000)

  it('does not auto-convert a queued file added to an already-converted batch (#464)', async () => {
    // Mixed batch: one item already converted, a second dropped in and still
    // queued. Toggling an option must not silently convert the queued file; the
    // auto-refresh only fires when every item has already produced a result.
    const user = userEvent.setup()
    render(wrap(<MdToPdf />, 'en'))

    // Convert a first file so the batch has a processed item.
    fireEvent.change(screen.getByLabelText('Pasted markdown'), { target: { value: '# Hi' } })
    await user.click(screen.getByRole('button', { name: 'Convert' }))
    await waitFor(() => expect(convertMdToPdf).toHaveBeenCalledTimes(1), { timeout: 5000 })

    // Add a second file; it stays queued (no explicit Convert).
    const file = new File(['# Later'], 'later.md', { type: 'text/markdown' })
    fireEvent.drop(screen.getByLabelText('Drop a Markdown file or click to choose'), {
      dataTransfer: { files: [file], items: [] as unknown as DataTransferItemList },
    })
    await screen.findByTitle('later.md')

    // Toggling must not convert the queued file: the call count stays at 1.
    await user.click(screen.getByRole('switch', { name: /render mermaid/i }))
    await new Promise((r) => setTimeout(r, 50))
    expect(convertMdToPdf).toHaveBeenCalledTimes(1)
  }, 10000)

  it('re-renders completed items with the current option when converting a mixed batch (#464)', async () => {
    // Convert one file, add a second, flip the option, then Convert all. Every
    // resulting PDF must use the current option, not a mix of old and new, so
    // downloads and the ZIP stay consistent with the visible setting.
    const user = userEvent.setup()
    render(wrap(<MdToPdf />, 'en'))

    const fileA = new File(['# A'], 'a.md', { type: 'text/markdown' })
    fireEvent.drop(screen.getByLabelText('Drop a Markdown file or click to choose'), {
      dataTransfer: { files: [fileA], items: [] as unknown as DataTransferItemList },
    })
    await screen.findByTitle('a.md')
    await user.click(screen.getByRole('button', { name: 'Convert all' }))
    await waitFor(() => expect(convertMdToPdf).toHaveBeenCalledTimes(1), { timeout: 5000 })
    expect(vi.mocked(convertMdToPdf).mock.calls.at(-1)![1]).toMatchObject({ render_mermaid: false })

    // Add a second file (queued) and turn Mermaid on; the auto-run stays suppressed.
    const fileB = new File(['# B'], 'b.md', { type: 'text/markdown' })
    fireEvent.drop(screen.getByLabelText('Drop a Markdown file or click to choose'), {
      dataTransfer: { files: [fileB], items: [] as unknown as DataTransferItemList },
    })
    await screen.findByTitle('b.md')
    await user.click(screen.getByRole('switch', { name: /render mermaid/i }))
    await new Promise((r) => setTimeout(r, 50))
    expect(convertMdToPdf).toHaveBeenCalledTimes(1)

    // Convert all rebuilds the mixed batch so both PDFs render with Mermaid on.
    vi.mocked(convertMdToPdf).mockClear()
    await user.click(screen.getByRole('button', { name: 'Convert all' }))
    await waitFor(() => expect(convertMdToPdf).toHaveBeenCalledTimes(2), { timeout: 5000 })
    for (const call of vi.mocked(convertMdToPdf).mock.calls) {
      expect(call[1]).toMatchObject({ render_mermaid: true })
    }
  }, 10000)
})
