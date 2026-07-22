import { useRef, useState, type FormEvent } from 'react'
import { useTranslation } from '../i18n'
import type { Preset } from '../lib/presets'
import { Button } from './Button'
import './PresetChips.css'

interface PresetChipsProps {
  presets: Preset[]
  activeId: string | null
  atCap: boolean
  onApply: (preset: Preset) => void
  onDelete: (id: string) => void
  onSave: (name: string) => void
  onImport: (file: File) => void
  onExport: () => void
  /** A conversion is running: applying a preset would change options mid-run, so
   *  the apply chips are disabled (mirrors the disabled theme picker). */
  busy?: boolean
}

export function PresetChips({
  presets,
  activeId,
  atCap,
  onApply,
  onDelete,
  onSave,
  onImport,
  onExport,
  busy = false,
}: PresetChipsProps) {
  const { t } = useTranslation()
  const h = t.presets
  const [naming, setNaming] = useState(false)
  const [name, setName] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  function submitName(e: FormEvent) {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    onSave(trimmed)
    setName('')
    setNaming(false)
  }

  return (
    <section className="presets" aria-label={h.title}>
      <div className="presets__head">
        <span className="presets__eyebrow">{h.title}</span>
        {presets.length > 0 && <span className="presets__count">{h.count(presets.length)}</span>}
        <div className="presets__io">
          {/* Hidden file input driven by a real button, never a clickable div. */}
          <input
            ref={fileRef}
            type="file"
            accept="application/json"
            className="visually-hidden"
            tabIndex={-1}
            aria-hidden="true"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) onImport(file)
              e.target.value = '' // let the same file be re-imported
            }}
          />
          <Button
            variant="ghost"
            className="presets__io-btn"
            onClick={() => fileRef.current?.click()}
          >
            {h.import}
          </Button>
          {presets.length > 0 && (
            <Button variant="ghost" className="presets__io-btn" onClick={onExport}>
              {h.export}
            </Button>
          )}
        </div>
      </div>

      <ul className="preset-row">
        {presets.map((preset) => (
          <li key={preset.id} className="preset-item">
            <button
              type="button"
              className={`preset-chip${preset.id === activeId ? ' is-active' : ''}`}
              aria-current={preset.id === activeId ? 'true' : undefined}
              aria-label={h.applyLabel(preset.name)}
              disabled={busy}
              onClick={() => onApply(preset)}
            >
              {preset.name}
            </button>
            <button
              type="button"
              className="preset-chip__del"
              aria-label={h.deleteLabel(preset.name)}
              onClick={() => onDelete(preset.id)}
            >
              <span aria-hidden="true">×</span>
            </button>
          </li>
        ))}

        {naming ? (
          <li className="preset-item">
            <form className="preset-name-form" onSubmit={submitName}>
              <input
                className="preset-name-input"
                aria-label={h.namePlaceholder}
                placeholder={h.namePlaceholder}
                value={name}
                autoFocus
                maxLength={40}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Escape') {
                    setNaming(false)
                    setName('')
                  }
                }}
              />
              <Button type="submit" variant="ghost" className="preset-chip is-add" disabled={!name.trim()}>
                {h.saveConfirm}
              </Button>
            </form>
          </li>
        ) : (
          <li className="preset-item">
            <button
              type="button"
              className="preset-chip is-add"
              disabled={atCap}
              onClick={() => setNaming(true)}
            >
              {h.save}
            </button>
          </li>
        )}
      </ul>

      {atCap && (
        <p className="presets__warn" role="status">
          {h.atCap}
        </p>
      )}
      {presets.length === 0 && !naming && <p className="presets__empty">{h.empty}</p>}
    </section>
  )
}
