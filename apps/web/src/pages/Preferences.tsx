import type { ReactNode } from 'react'
import { useTranslation } from '../i18n'
import { useTheme } from '../theme'
import { usePrefs } from '../hooks/usePrefs'
import { useThemes } from '../hooks/useThemes'
import { clearAllPrefs, PAGE_SIZES, type PageSize } from '../lib/prefs'
import { Button } from '../components/Button'
import { Segmented } from '../components/Segmented'
import { ThemePicker } from '../components/ThemePicker'
import type { Locale } from '../i18n/dictionaries'
import './Preferences.css'

const ACCENTS = [
  { value: '#c8362f', key: 'brand' },
  { value: '#1f5e9e', key: 'blue' },
  { value: '#2e7d4a', key: 'green' },
  { value: '#1a1a1a', key: 'graphite' },
] as const

const AUDIT_REPORT_URL =
  'https://github.com/vinicq/md-bridge/blob/main/scripts/audit-deps.py'

function Row({
  label,
  hint,
  control,
}: {
  label: string
  hint: string
  control: ReactNode
}) {
  return (
    <div className="pref-row">
      <div className="pref-row__text">
        <b className="pref-row__label">{label}</b>
        <p className="pref-row__hint">{hint}</p>
      </div>
      <div className="pref-row__control">{control}</div>
    </div>
  )
}

function Switch({
  checked,
  onChange,
  label,
  onText,
  offText,
}: {
  checked: boolean
  onChange: (next: boolean) => void
  label: string
  onText: string
  offText: string
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
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

export function Preferences() {
  const { t, locale, setLocale, locales } = useTranslation()
  const { theme, toggleTheme } = useTheme()
  const { prefs, set } = usePrefs()
  const { themes, status, error } = useThemes()
  const p = t.preferences

  function handleReset() {
    clearAllPrefs()
    // Reinitialize both providers and the prefs store from a clean slate. The
    // simplest correct reset: everything re-detects on the next boot.
    window.location.reload()
  }

  return (
    <div className="page container preferences">
      <header className="page__head">
        <h1>{p.title}</h1>
        <p className="preferences__sub">{p.subtitle}</p>
      </header>

      <section className="pref-section" aria-label={p.sections.defaults}>
        <h2 className="pref-section__head">// {p.sections.defaults}</h2>

        <Row
          label={p.defaultLanguage.label}
          hint={p.defaultLanguage.hint}
          control={
            <Segmented<Locale>
              label={p.defaultLanguage.label}
              options={locales.map(({ code, label }) => ({ value: code, label }))}
              value={locale}
              onChange={setLocale}
            />
          }
        />

        <Row
          label={p.defaultPdfTheme.label}
          hint={p.defaultPdfTheme.hint}
          control={
            <ThemePicker
              themes={themes}
              value={prefs.defaultPdfTheme}
              onChange={(slug) => set({ defaultPdfTheme: slug })}
              label={p.defaultPdfTheme.label}
              loadingLabel={t.themePicker.loading}
              loading={status === 'loading'}
              loadError={status === 'error' ? error : null}
            />
          }
        />

        <Row
          label={p.pageSize.label}
          hint={p.pageSize.hint}
          control={
            <Segmented<PageSize>
              label={p.pageSize.label}
              options={PAGE_SIZES.map((size) => ({ value: size, label: size }))}
              value={prefs.pageSize}
              onChange={(pageSize) => set({ pageSize })}
            />
          }
        />

        <Row
          label={p.previewNewTab.label}
          hint={p.previewNewTab.hint}
          control={
            <Switch
              checked={prefs.previewNewTab}
              onChange={(previewNewTab) => set({ previewNewTab })}
              label={p.previewNewTab.label}
              onText={p.on}
              offText={p.off}
            />
          }
        />
      </section>

      <section className="pref-section" aria-label={p.sections.ui}>
        <h2 className="pref-section__head">// {p.sections.ui}</h2>

        <Row
          label={p.darkMode.label}
          hint={p.darkMode.hint}
          control={
            <Switch
              checked={theme === 'dark'}
              onChange={toggleTheme}
              label={p.darkMode.label}
              onText={p.on}
              offText={p.off}
            />
          }
        />

        <Row
          label={p.accent.label}
          hint={p.accent.hint}
          control={
            <div className="pref-swatches" role="radiogroup" aria-label={p.accent.label}>
              {ACCENTS.map(({ value, key }) => {
                const selected = prefs.accent.toLowerCase() === value
                return (
                  <button
                    key={value}
                    type="button"
                    role="radio"
                    aria-checked={selected}
                    aria-label={p.accent.swatch[key]}
                    className={`pref-swatch ${selected ? 'is-on' : ''}`}
                    style={{ background: value }}
                    onClick={() => set({ accent: value })}
                  >
                    {selected && (
                      <span className="pref-swatch__check" aria-hidden="true">
                        ✓
                      </span>
                    )}
                  </button>
                )
              })}
            </div>
          }
        />

        <Row
          label={p.reduceMotion.label}
          hint={p.reduceMotion.hint}
          control={
            <Switch
              checked={prefs.reduceMotion === true}
              onChange={(on) => set({ reduceMotion: on ? true : null })}
              label={p.reduceMotion.label}
              onText={p.on}
              offText={p.off}
            />
          }
        />
      </section>

      <section className="pref-section" aria-label={p.sections.privacy}>
        <h2 className="pref-section__head">// {p.sections.privacy}</h2>
        <div className="pref-badge">
          <span className="pref-badge__mark" aria-hidden="true">
            ∅
          </span>
          <div>
            <b className="pref-badge__title">{p.privacy.badge}</b>
            <p className="pref-badge__body">
              {p.privacy.verified}{' '}
              <a href={AUDIT_REPORT_URL} target="_blank" rel="noreferrer">
                {p.privacy.viewReport} →
              </a>
            </p>
          </div>
        </div>
      </section>

      <div className="preferences__actions">
        <Button variant="destructive" onClick={handleReset}>
          {p.reset}
        </Button>
      </div>
    </div>
  )
}
