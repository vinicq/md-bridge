import { describe, expect, it } from 'vitest'
import { DICTIONARIES, type Locale } from '../../src/i18n/dictionaries'
import { PREVIEW_SAMPLES, type PreviewSampleId } from '../../src/lib/previewSamples'

// #398: the shared preview samples consumed by the theme library (#392) and the
// md-to-pdf live preview (#397). Content is fixed Markdown; only the label is
// localized. This fails on main where the module and labels do not exist.

const EXPECTED_IDS: PreviewSampleId[] = [
  'document',
  'article',
  'resume',
  'email',
  'contract',
  'blog',
]

describe('preview samples (#398)', () => {
  it('exposes the six samples in order, each with a Markdown body', () => {
    expect(PREVIEW_SAMPLES.map((s) => s.id)).toEqual(EXPECTED_IDS)
    for (const sample of PREVIEW_SAMPLES) {
      expect(sample.markdown.trim().length).toBeGreaterThan(0)
      // Every sample opens with a top-level heading so a theme's h1 shows.
      expect(sample.markdown.trimStart().startsWith('# ')).toBe(true)
    }
  })

  it('has a localized label for every sample in every locale', () => {
    const locales: Locale[] = ['en', 'pt', 'es']
    for (const locale of locales) {
      const labels = DICTIONARIES[locale].previewSamples
      for (const id of EXPECTED_IDS) {
        expect(labels[id], `${locale}.previewSamples.${id}`).toBeTruthy()
      }
    }
  })
})
