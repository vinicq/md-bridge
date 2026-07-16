import { afterEach, describe, expect, expectTypeOf, it, vi } from 'vitest'
import {
  ApiError,
  convertPdfToMd,
  fetchThemes,
  type PdfToMdResponse,
  type Theme,
} from '../../src/lib/api'
import type { components } from '../../src/lib/api-types'

// #32: the request/response types are generated from the FastAPI OpenAPI schema.
// These tests pin the observable call shape (endpoint, method, FormData body,
// error envelope) so the generated-types migration stays behavior-identical, and
// assert at the type level that the exported types line up with the schema.

function okResponse(body: unknown): Response {
  return { ok: true, status: 200, json: async () => body } as Response
}

function errorResponse(status: number, body: unknown): Response {
  return { ok: false, status, statusText: 'err', json: async () => body } as Response
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('api typed client (#32)', () => {
  it('exports response types that match the generated schema', () => {
    expectTypeOf<PdfToMdResponse>().toMatchObjectType<
      components['schemas']['PdfToMdResponse']
    >()
    expectTypeOf<Theme>().toEqualTypeOf<components['schemas']['ThemeInfo']>()
  })

  it('posts pdf-to-md as multipart and returns the typed shape', async () => {
    const body: PdfToMdResponse = {
      md: '# Title\n\n> quote',
      front_matter: { title: 'Title' },
      warnings: [],
      stats: { headings: 1, tables: 0, bullets: 0 },
      ocr_applied: false,
    }
    const fetchMock = vi.fn(async () => okResponse(body))
    vi.stubGlobal('fetch', fetchMock)

    const file = new File(['%PDF-1.7'], 'doc.pdf', { type: 'application/pdf' })
    const result = await convertPdfToMd(file, { detect_blockquotes: true })

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/pdf-to-md')
    expect(init?.method).toBe('POST')
    expect(init?.body).toBeInstanceOf(FormData)
    const fd = init?.body as FormData
    expect(fd.get('file')).toBe(file)
    expect(JSON.parse(fd.get('options') as string)).toEqual({ detect_blockquotes: true })
    expect(result.md).toContain('> quote')
    expect(result.stats.headings).toBe(1)
  })

  it('throws ApiError carrying the envelope code and message on failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        errorResponse(400, { error: { code: 'wrong_file_type', message: 'not a pdf' } }),
      ),
    )
    const file = new File(['x'], 'notes.txt', { type: 'text/plain' })
    await expect(convertPdfToMd(file)).rejects.toMatchObject({
      name: expect.any(String),
      code: 'wrong_file_type',
      status: 400,
      message: 'not a pdf',
    })
    await expect(convertPdfToMd(file)).rejects.toBeInstanceOf(ApiError)
  })

  it('fetches themes as a typed list', async () => {
    const themes: Theme[] = [{ slug: 'default', name: 'Default', description: '', family: 'general' }]
    vi.stubGlobal('fetch', vi.fn(async () => okResponse(themes)))
    const result = await fetchThemes()
    expect(result[0].slug).toBe('default')
  })
})
