export interface PdfToMdOptions {
  page_break?: boolean
  with_images?: boolean
  front_matter?: boolean
  lang?: string
}

export interface MdToPdfOptions {
  lang?: string
  theme?: string
}

export interface Theme {
  slug: string
  name: string
  description: string
  family: string
}

export interface FrontMatter {
  title?: string
  author?: string
  date?: string
  source?: string
  pages?: number
}

export interface ConvertStats {
  headings: number
  tables: number
  bullets: number
}

export interface PdfToMdResponse {
  md: string
  front_matter: FrontMatter
  warnings: string[]
  stats: ConvertStats
}

export interface FontUsage {
  name: string
  size: number
  count: number
  sample: string
}

export interface InspectPdfResponse {
  pages: number
  body_size_pt: number
  heading_sizes_pt: number[]
  fonts: FontUsage[]
  tagged: boolean
  needs_ocr: boolean
}

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

export async function fetchThemes(signal?: AbortSignal): Promise<Theme[]> {
  const resp = await fetch('/api/themes', { signal })
  if (!resp.ok) await readError(resp)
  return (await resp.json()) as Theme[]
}

export async function inspectPdf(file: File, signal?: AbortSignal): Promise<InspectPdfResponse> {
  const fd = new FormData()
  fd.append('file', file)
  const resp = await fetch('/api/inspect-pdf', { method: 'POST', body: fd, signal })
  if (!resp.ok) await readError(resp)
  return (await resp.json()) as InspectPdfResponse
}
