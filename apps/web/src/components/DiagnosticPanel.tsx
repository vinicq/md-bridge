import type { InspectPdfResponse } from '../lib/api'
import { useTranslation } from '../i18n'
import './DiagnosticPanel.css'

interface DiagnosticPanelProps {
  data: InspectPdfResponse | null
  loading?: boolean
  error?: string | null
  // `card` (default) is the sidebar block; `strip` lays the pairs out inline.
  layout?: 'card' | 'strip'
}

export function DiagnosticPanel({ data, loading, error, layout = 'card' }: DiagnosticPanelProps) {
  const { t } = useTranslation()
  const variant = layout === 'strip' ? ' diag--strip' : ''
  if (error) {
    return (
      <aside className={`diag diag--error${variant}`} role="alert">
        {error}
      </aside>
    )
  }
  if (loading) {
    return <aside className={`diag diag--muted${variant}`}>{t.diag.loading}</aside>
  }
  if (!data) {
    return <aside className={`diag diag--muted${variant}`}>{t.diag.empty}</aside>
  }

  return (
    <aside className={`diag${variant}`} aria-label={t.diag.title}>
      <dl className="diag__grid">
        <div>
          <dt>{t.diag.pages}</dt>
          <dd>{data.pages}</dd>
        </div>
        <div className="diag__cell--secondary">
          <dt>{t.diag.body}</dt>
          <dd>{data.body_size_pt.toFixed(1)} pt</dd>
        </div>
        <div className="diag__cell--secondary">
          <dt>{t.diag.headings}</dt>
          <dd>
            {data.heading_sizes_pt.length === 0
              ? '—'
              : data.heading_sizes_pt.map((s) => `${s.toFixed(1)}pt`).join(', ')}
          </dd>
        </div>
        <div>
          <dt>{t.diag.tagged}</dt>
          <dd>{data.tagged ? t.diag.yes : t.diag.no}</dd>
        </div>
      </dl>
      {data.needs_ocr && <p className="diag__warn">{t.diag.needsOcr}</p>}
      {data.fonts.length > 0 && (
        <details className="diag__fonts">
          <summary>{t.diag.fonts(data.fonts.length)}</summary>
          <ul>
            {data.fonts.slice(0, 8).map((f) => (
              <li key={`${f.name}-${f.size}`}>
                <code>{f.name}</code> · {f.size.toFixed(1)}pt · {f.count} {t.diag.chars}
              </li>
            ))}
          </ul>
        </details>
      )}
    </aside>
  )
}
