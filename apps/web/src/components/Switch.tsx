import './setting-controls.css'

export function Switch({
  checked,
  onChange,
  label,
  onText,
  offText,
  describedBy,
  disabled,
}: {
  checked: boolean
  onChange: (next: boolean) => void
  label: string
  onText: string
  offText: string
  describedBy?: string
  disabled?: boolean
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      aria-describedby={describedBy}
      disabled={disabled}
      className={`pref-switch ${checked ? 'is-on' : ''}`}
      onClick={() => onChange(!checked)}
    >
      <span className="pref-switch__track" aria-hidden="true">
        <span className="pref-switch__thumb" />
      </span>
      <span className="pref-switch__state">{checked ? onText : offText}</span>
    </button>
  )
}
