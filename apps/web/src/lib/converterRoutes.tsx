import type { ComponentType } from 'react'
import { MdToPdf } from '../pages/MdToPdf'
import { PdfToMd } from '../pages/PdfToMd'

// Single source of truth for which conversion pairs have a converter PAGE in the
// SPA, keyed by the registry slug. The router and the format hub both read this.
//
// "Shipped in the API" (GET /api/formats / the backend registry) and "has a UI
// page" are two different facts. md-to-docx ships in the API (#60) but has no
// page yet, so the format hub must not link it to a dead /convert/md-to-docx
// route (#237). Adding a converter page = one entry here; the router gains the
// route and the hub starts linking the cell, with no other change.
export const CONVERTER_PAGES: Record<string, ComponentType> = {
  'pdf-to-md': PdfToMd,
  'md-to-pdf': MdToPdf,
}

export function hasConverterPage(slug: string): boolean {
  return Object.prototype.hasOwnProperty.call(CONVERTER_PAGES, slug)
}
