import type { ComponentType } from 'react'
import { MdToDocx } from '../pages/MdToDocx'
import { MdToPdf } from '../pages/MdToPdf'
import { PdfToMd } from '../pages/PdfToMd'

// Single source of truth for which conversion pairs have a converter PAGE in the
// SPA, keyed by the registry slug. The router and the format hub both read this.
//
// "Shipped in the API" (GET /api/formats / the backend registry) and "has a UI
// page" are two different facts. Adding a converter page = one entry here; the
// router gains the route and the format hub starts linking the cell, with no
// other change. md-to-docx (#60, #276) now has its page, so its hub cell flips
// from non-navigable to an internal link automatically.
export const CONVERTER_PAGES: Record<string, ComponentType> = {
  'pdf-to-md': PdfToMd,
  'md-to-pdf': MdToPdf,
  'md-to-docx': MdToDocx,
}

export function hasConverterPage(slug: string): boolean {
  return Object.prototype.hasOwnProperty.call(CONVERTER_PAGES, slug)
}
