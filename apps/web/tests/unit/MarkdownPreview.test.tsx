import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { MarkdownPreview } from '../../src/components/MarkdownPreview'

describe('MarkdownPreview', () => {
  it('renders the empty placeholder when there is no content', () => {
    render(<MarkdownPreview markdown="" empty="Nothing yet" />)
    expect(screen.getByText('Nothing yet')).toBeInTheDocument()
  })

  it('renders headings and paragraphs from markdown', () => {
    const md = '# Title\n\nA paragraph.'
    render(<MarkdownPreview markdown={md} />)
    expect(screen.getByRole('heading', { level: 1, name: 'Title' })).toBeInTheDocument()
    expect(screen.getByText('A paragraph.')).toBeInTheDocument()
  })

  it('renders fenced code blocks as <pre><code>', () => {
    render(<MarkdownPreview markdown={'```js\nconst x = 1\n```'} />)
    expect(screen.getByText(/const x = 1/)).toBeInTheDocument()
  })

  it('uses the empty string fallback when no empty prop is given', () => {
    const { container } = render(<MarkdownPreview markdown="" />)
    const wrapper = container.querySelector('.md-preview--empty')
    expect(wrapper).not.toBeNull()
  })

  it('renders GFM tables as a <table> with column headers', () => {
    const md = '| Col A | Col B |\n|---|---|\n| 1 | 2 |'
    render(<MarkdownPreview markdown={md} />)
    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Col A' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Col B' })).toBeInTheDocument()
    expect(screen.getByRole('cell', { name: '1' })).toBeInTheDocument()
  })
})
