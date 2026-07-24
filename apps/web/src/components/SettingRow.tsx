import type { ReactNode } from 'react'
import './setting-controls.css'

export function SettingRow({
  label,
  hint,
  hintId,
  control,
}: {
  label: string
  hint: string
  // When set, the hint carries this id so a control can point at it with
  // aria-describedby, making the scope line audible to a screen reader.
  hintId?: string
  control: ReactNode
}) {
  return (
    <div className="pref-row">
      <div className="pref-row__text">
        <b className="pref-row__label">{label}</b>
        <p className="pref-row__hint" id={hintId}>
          {hint}
        </p>
      </div>
      <div className="pref-row__control">{control}</div>
    </div>
  )
}
