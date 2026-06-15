import { useId } from 'react'
import type { Theme } from '../lib/api'
import './ThemePicker.css'

export interface ThemePickerProps {
  themes: Theme[]
  /** The selected theme slug. */
  value: string
  onChange: (slug: string) => void
  /** Group label (localized chrome; theme names come from the API). */
  label: string
  /** Placeholder shown while themes are loading. */
  loadingLabel: string
  /** Disable selection (e.g. while a conversion is running). */
  disabled?: boolean
  /** Loading / error state from the theme fetch. */
  loading?: boolean
  loadError?: string | null
}

export function ThemePicker({
  themes,
  value,
  onChange,
  label,
  loadingLabel,
  disabled = false,
  loading = false,
  loadError = null,
}: ThemePickerProps) {
  const selectId = useId()
  const isDisabled = disabled || loading

  return (
    <div className="theme-picker">
      <label className="theme-picker__label" htmlFor={selectId}>
        {label}
      </label>

      {loadError && (
        <p className="theme-picker__error" role="alert">
          {loadError}
        </p>
      )}

      <select
        id={selectId}
        className="theme-picker__select"
        value={loading ? '' : value}
        onChange={(e) => onChange(e.target.value)}
        disabled={isDisabled}
      >
        {loading && (
          <option value="" disabled>
            {loadingLabel}
          </option>
        )}
        {themes.map((theme) => (
          <option key={theme.slug} value={theme.slug}>
            {theme.name}
          </option>
        ))}
      </select>
    </div>
  )
}
