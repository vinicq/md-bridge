import type { Theme } from '../lib/api'
import './ThemePicker.css'

export interface ThemePickerProps {
  themes: Theme[]
  /** The selected theme slug. */
  value: string
  onChange: (slug: string) => void
  /** Group label (localized chrome; theme names come from the API). */
  label: string
  /** "Browse all themes" link text and target (F2, may be a placeholder route). */
  browseLabel: string
  browseHref: string
}

// A swatch hint driven by the theme's typographic family rather than a live
// render of the user's markdown (that deep preview is F2, out of scope here).
function swatchFontFamily(family: string): string {
  return family === 'serif' ? 'Georgia, "Times New Roman", serif' : 'var(--font-body)'
}

export function ThemePicker({
  themes,
  value,
  onChange,
  label,
  browseLabel,
  browseHref,
}: ThemePickerProps) {
  return (
    <fieldset className="theme-picker">
      <legend className="theme-picker__legend">{label}</legend>

      <div className="theme-picker__grid">
        {themes.map((theme) => {
          const active = theme.slug === value
          return (
            <label
              key={theme.slug}
              className={`theme-tile ${active ? 'is-active' : ''}`.trim()}
            >
              <span className="theme-tile__head">
                <input
                  type="radio"
                  name="md-to-pdf-theme"
                  value={theme.slug}
                  checked={active}
                  onChange={() => onChange(theme.slug)}
                  className="theme-tile__input"
                />
                <span className="theme-tile__name">{theme.name}</span>
                <span className="theme-tile__family">{theme.family}</span>
              </span>
              <span
                className="theme-tile__swatch"
                style={{ fontFamily: swatchFontFamily(theme.family) }}
                aria-hidden="true"
              >
                <span className="theme-tile__swatch-h">Sample heading</span>
                <span className="theme-tile__swatch-b">Body text in this theme.</span>
              </span>
            </label>
          )
        })}
      </div>

      <a className="theme-picker__browse" href={browseHref}>
        {browseLabel}
      </a>
    </fieldset>
  )
}
