import './OptionsPanel.css'

export type OptionToggle = {
  id: string
  kind: 'toggle'
  label: string
  tooltip?: string
  disabled?: boolean
}

export type OptionSelect = {
  id: string
  kind: 'select'
  label: string
  tooltip?: string
  disabled?: boolean
  options: { value: string; label: string }[]
}

export type OptionField = OptionToggle | OptionSelect

export interface OptionsPanelProps {
  /** Group label rendered as the fieldset legend. */
  legend: string
  fields: OptionField[]
  values: Record<string, boolean | string | number>
  onChange: (id: string, value: boolean | string) => void
  /** Disable all controls (e.g. while a conversion runs). */
  disabled?: boolean
}

// A reusable, data-driven per-conversion options panel. Each page passes the
// fields its converter actually honors, so the panel never shows an inert
// control (#59). The tooltip uses the native `title` attribute fallback rather
// than inventing new chrome.
export function OptionsPanel({ legend, fields, values, onChange, disabled = false }: OptionsPanelProps) {
  return (
    <fieldset className="options-panel" disabled={disabled}>
      <legend className="options-panel__legend">{legend}</legend>

      <div className="options-panel__grid">
        {fields.map((field) => {
          if (field.kind === 'toggle') {
            return (
              <label key={field.id} className="options-panel__row" title={field.tooltip}>
                <input
                  type="checkbox"
                  checked={Boolean(values[field.id])}
                  disabled={field.disabled}
                  onChange={(e) => onChange(field.id, e.target.checked)}
                />
                <span className="options-panel__label">{field.label}</span>
              </label>
            )
          }
          return (
            <label key={field.id} className="options-panel__row options-panel__row--select" title={field.tooltip}>
              <span className="options-panel__label">{field.label}</span>
              <select
                className="options-panel__select"
                value={String(values[field.id])}
                disabled={field.disabled}
                onChange={(e) => onChange(field.id, e.target.value)}
              >
                {field.options.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </label>
          )
        })}
      </div>
    </fieldset>
  )
}
