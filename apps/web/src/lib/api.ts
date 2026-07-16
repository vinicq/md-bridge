import type { components } from './api-types'

// Response and domain types are generated from the FastAPI OpenAPI schema
// (`src/lib/openapi.json` -> `src/lib/api-types.ts`). Regenerate with
// `npm run gen:api` after the backend schema changes; CI fails on drift. A few
// fields are refined below where the backend's runtime contract is tighter than
// the schema advertises.
type Schemas = components['schemas']

// Request option payloads are NOT part of the OpenAPI schema: the endpoints take
// them as an opaque JSON string form field (`options`), so there is nothing to
// generate. They stay hand-typed here.
interface PdfToMdOptions {
  page_break?: boolean
  with_images?: boolean
  front_matter?: boolean
  detect_blockquotes?: boolean
  cluster_headings?: boolean
  subtract_running_furniture?: boolean
  allow_html?: string[]
  preserve_line_breaks?: boolean
  max_heading_level?: number
  footnote_pairing?: boolean
  lang?: string
}

export interface RunningContent {
  left: string
  center: string
  right: string
}

export interface PageSetup {
  page_size: 'A4' | 'Letter' | 'Legal'
  margins: 'tight' | 'normal' | 'loose'
  header?: RunningContent | null
  footer?: RunningContent | null
}

export interface MdToPdfOptions {
  lang?: string
  theme?: string
  page_setup?: PageSetup | null
}

export interface MdToDocxOptions {
  lang?: string
}

export type Theme = Schemas['ThemeInfo']

export type FormatStatus = 'shipped' | 'in-pr' | 'roadmap' | 'wanted'

// FastAPI types `status` as an open string; the registry only ever emits the
// four values above, and the matrix maps each to an i18n label.
export type Format = Omit<Schemas['FormatInfo'], 'status'> & { status: FormatStatus }

export type FrontMatter = Schemas['FrontMatter']

export type ConvertStats = Schemas['ConvertStats']

// The backend always serializes `front_matter`, `stats`, and `warnings` (they
// are Pydantic model defaults), though the schema marks them optional because a
// default makes a field non-required. Keep them required for consumers.
export type PdfToMdResponse = Schemas['PdfToMdResponse'] &
  Required<Pick<Schemas['PdfToMdResponse'], 'front_matter' | 'stats' | 'warnings'>>

export type FontUsage = Schemas['FontUsage']

export type InspectPdfResponse = Schemas['InspectPdfResponse']

export interface ApiErrorBody {
  error: {
    code: string
    message: string
    detail?: unknown
  }
}

export class ApiError extends Error {
  code: string
  status: number
  detail: unknown

  constructor(status: number, code: string, message: string, detail: unknown = undefined) {
    super(message)
    this.status = status
    this.code = code
    this.detail = detail
  }
}

async function readError(response: Response): Promise<never> {
  let body: ApiErrorBody | undefined
  try {
    body = (await response.json()) as ApiErrorBody
  } catch {
    body = undefined
  }
  const code = body?.error?.code ?? 'http_error'
  const message = body?.error?.message ?? response.statusText ?? 'Request failed'
  throw new ApiError(response.status, code, message, body?.error?.detail)
}

export async function convertPdfToMd(
  file: File,
  options: PdfToMdOptions = {},
  signal?: AbortSignal,
): Promise<PdfToMdResponse> {
  const fd = new FormData()
  fd.append('file', file)
  if (Object.keys(options).length > 0) {
    fd.append('options', JSON.stringify(options))
  }
  const resp = await fetch('/api/pdf-to-md', { method: 'POST', body: fd, signal })
  if (!resp.ok) await readError(resp)
  return (await resp.json()) as PdfToMdResponse
}

export async function convertMdToPdf(
  file: File,
  options: MdToPdfOptions = {},
  signal?: AbortSignal,
): Promise<Blob> {
  const fd = new FormData()
  fd.append('file', file)
  if (Object.keys(options).length > 0) {
    fd.append('options', JSON.stringify(options))
  }
  const resp = await fetch('/api/md-to-pdf', { method: 'POST', body: fd, signal })
  if (!resp.ok) await readError(resp)
  return resp.blob()
}

export async function convertMdToDocx(
  file: File,
  options: MdToDocxOptions = {},
  signal?: AbortSignal,
): Promise<Blob> {
  const fd = new FormData()
  fd.append('file', file)
  if (Object.keys(options).length > 0) {
    fd.append('options', JSON.stringify(options))
  }
  const resp = await fetch('/api/md-to-docx', { method: 'POST', body: fd, signal })
  if (!resp.ok) await readError(resp)
  return resp.blob()
}

export async function fetchThemes(signal?: AbortSignal): Promise<Theme[]> {
  const resp = await fetch('/api/themes', { signal })
  if (!resp.ok) await readError(resp)
  return (await resp.json()) as Theme[]
}

export async function fetchFormats(signal?: AbortSignal): Promise<Format[]> {
  const resp = await fetch('/api/formats', { signal })
  if (!resp.ok) await readError(resp)
  return (await resp.json()) as Format[]
}

// The theme's own overlay stylesheet as text/css. The theme library stacks it
// after default.css to preview the render, and shows it read-only. Not part of
// the JSON schema (it is a text/css response), so it stays hand-written.
export async function fetchThemeCss(slug: string, signal?: AbortSignal): Promise<string> {
  const resp = await fetch(`/api/themes/${encodeURIComponent(slug)}/css`, { signal })
  if (!resp.ok) await readError(resp)
  return resp.text()
}

export async function inspectPdf(file: File, signal?: AbortSignal): Promise<InspectPdfResponse> {
  const fd = new FormData()
  fd.append('file', file)
  const resp = await fetch('/api/inspect-pdf', { method: 'POST', body: fd, signal })
  if (!resp.ok) await readError(resp)
  return (await resp.json()) as InspectPdfResponse
}
