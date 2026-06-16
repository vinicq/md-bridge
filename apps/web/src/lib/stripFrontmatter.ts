/**
 * Strip YAML front matter from a markdown string.
 * Only strips if the document starts with exactly `---` on the first line.
 * A `---` anywhere else (thematic break mid-document) is left untouched.
 */
export function stripFrontmatter(md: string): string {
  if (!/^---[ \t]*\r?\n/.test(md)) return md

  const afterOpen = md.replace(/^---[ \t]*\r?\n/, '')
  const closeMatch = afterOpen.match(/^(?:---|\.\.\.)\s*$/m)
  if (!closeMatch || closeMatch.index === undefined) return md

  return afterOpen
    .slice(closeMatch.index)
    .replace(/^(?:---|\.\.\.)[^\n]*\n?/, '')
}
