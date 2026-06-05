import { useId } from 'react'
import { Link } from 'react-router-dom'
import { useFormats } from '../hooks/useFormats'
import { useTranslation } from '../i18n'
import type { Format, FormatStatus } from '../lib/api'
import { hasConverterPage } from '../lib/converterRoutes'
import './FormatMatrix.css'

// The format hub on Home (#237). Renders the conversion matrix straight from the
// GET /api/formats registry (#60), so a pair added on the server appears with no
// component change. Shipped pairs link to their converter route; planned pairs
// link to a prefilled feature request.

const REPO_ISSUES_NEW = 'https://github.com/vinicq/md-bridge/issues/new'

// Planned cells (endpoint null) point at the feature-request template with a
// prefilled "feature: <source>-to-<target>" title.
function requestHref(fmt: Format): string {
  const params = new URLSearchParams({
    template: 'feature_request.md',
    title: `feature: ${fmt.source}-to-${fmt.target}`,
  })
  return `${REPO_ISSUES_NEW}?${params.toString()}`
}

export function FormatMatrix() {
  const { t } = useTranslation()
  const { formats } = useFormats()
  const headingId = useId()
  const m = t.home.matrix

  // The API status enum (hyphenated) maps to an i18n label. Explicit lookup so
  // `in-pr` resolves to the `inPr` key rather than being derived blindly.
  const statusLabel: Record<FormatStatus, string> = {
    shipped: m.status.shipped,
    'in-pr': m.status.inPr,
    roadmap: m.status.roadmap,
    wanted: m.status.wanted,
  }

  // Nothing to show until the registry loads (or if the fetch fails); the
  // curated cards above stay regardless.
  if (formats.length === 0) return null

  return (
    <section className="home__matrix" aria-labelledby={headingId}>
      <h2 id={headingId}>{m.heading}</h2>
      <ul className="format-matrix">
        {formats.map((fmt) => (
          <li key={fmt.slug} className="format-cell">
            {fmt.endpoint && hasConverterPage(fmt.slug) ? (
              // A converter page exists for this pair: link to it. Route from the
              // slug, never the API endpoint (that is the POST target, not a
              // navigable page).
              <Link to={`/convert/${fmt.slug}`} className="format-cell__link">
                <span className="format-cell__cta">{m.openConverter}</span>
                <span className="format-cell__label">{fmt.label}</span>
              </Link>
            ) : fmt.endpoint ? (
              // Shipped in the API but no UI page yet (e.g. md-to-docx, #60). Do
              // NOT link a dead /convert route; show the pair non-navigable until
              // its page lands. The Shipped pill still tells the truth.
              <span className="format-cell__static">{fmt.label}</span>
            ) : (
              // Planned pair: link to a prefilled feature request.
              <a
                className="format-cell__link"
                href={requestHref(fmt)}
                target="_blank"
                rel="noopener noreferrer"
              >
                <span className="format-cell__cta">{m.requestPair}</span>
                <span className="format-cell__label">{fmt.label}</span>
                <span className="visually-hidden"> {m.newTab}</span>
              </a>
            )}
            <span className={`status-pill status-pill--${fmt.status}`}>
              {statusLabel[fmt.status]}
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}
