import { useTranslation } from '../i18n'
import { useTheme } from '../theme'
import { usePrefs } from '../hooks/usePrefs'
import { useThemes } from '../hooks/useThemes'
import { clearAllPrefs } from '../lib/prefs'
import { Button } from '../components/Button'
import { Switch } from '../components/Switch'
import { SettingRow } from '../components/SettingRow'
import { Segmented } from '../components/Segmented'
import { ThemePicker } from '../components/ThemePicker'
import type { Locale } from '../i18n/dictionaries'
import './Preferences.css'

function prefersReducedMotion(): boolean {
  return (
    typeof window !== 'undefined' &&
    !!window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  )
}

export function Preferences() {
  const { t, locale, setLocale, locales } = useTranslation()
  const { theme, toggleTheme } = useTheme()
  const { prefs, set } = usePrefs()
  const { themes, status, error } = useThemes()
  const p = t.preferences

  // The switch reflects the effective state: an explicit manual override, or
  // the OS request when the preference follows the OS (null). Announcing "Off"
  // while the OS reduces motion would lie to the screen reader (4.1.2).
  const reduceMotionOn = prefs.reduceMotion ?? prefersReducedMotion()

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

        <SettingRow
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

        <SettingRow
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
      </section>

      <section className="pref-section" aria-label={p.sections.ui}>
        <h2 className="pref-section__head">// {p.sections.ui}</h2>

        <SettingRow
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

        <SettingRow
          label={p.reduceMotion.label}
          hint={p.reduceMotion.hint}
          control={
            <Switch
              checked={reduceMotionOn}
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
            <p className="pref-badge__body">{p.privacy.body}</p>
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
