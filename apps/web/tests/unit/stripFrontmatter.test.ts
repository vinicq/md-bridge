import { describe, expect, it } from 'vitest'
import { stripFrontmatter } from '../../src/lib/stripFrontmatter'

describe('stripFrontmatter', () => {
  it('strips a leading YAML front matter block', () => {
    const md = '---\ntitle: Doc\nauthor: Jane\n---\n# Heading\n\nBody.'
    expect(stripFrontmatter(md)).toBe('# Heading\n\nBody.')
  })

  it('handles CRLF line endings', () => {
    const md = '---\r\ntitle: Doc\r\n---\r\n# Heading\r\n'
    expect(stripFrontmatter(md)).toBe('# Heading\r\n')
  })

  it('accepts a `...` close marker', () => {
    const md = '---\ntitle: Doc\n...\n# Heading\n'
    expect(stripFrontmatter(md)).toBe('# Heading\n')
  })

  it('passes through a document with no front matter', () => {
    const md = '# Heading\n\nJust body, no front matter.'
    expect(stripFrontmatter(md)).toBe(md)
  })

  it('leaves a mid-document thematic break untouched', () => {
    // The `---` here is a horizontal rule, not front matter: the doc does not
    // open with it, so nothing is stripped.
    const md = '# Heading\n\nIntro.\n\n---\n\nMore.'
    expect(stripFrontmatter(md)).toBe(md)
  })

  it('does not strip when the opening fence is never closed', () => {
    const md = '---\ntitle: Doc\n# Heading with no close fence\n'
    expect(stripFrontmatter(md)).toBe(md)
  })
})
