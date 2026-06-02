import { useCallback, useMemo, useState } from 'react'
import { DICTIONARIES, LOCALES, type Locale } from '../i18n/dictionaries'
import { useTranslation } from '../i18n'
import {
  computeCompletion,
  flattenDictionary,
  loadDraft,
  saveDraft,
  serializeDraftAsJson,
  serializeDraftAsTs,
  type FlatDict,
} from '../i18n/workshop'
import './LanguageWorkshop.css'

// English is the reference, so it is never a translation target.
const TARGET_LOCALES = LOCALES.filter((l) => l.code !== 'en')

export function LanguageWorkshop() {
  const { t } = useTranslation()
  const firstTarget = TARGET_LOCALES[0]?.code ?? 'pt'
  const [target, setTargetState] = useState<Locale>(firstTarget)
  // One draft map per locale, each loaded from localStorage the first time the
  // locale is selected. Kept in state (not an effect) so switching locales is a
  // pure event-handler update.
  const [drafts, setDrafts] = useState<Record<string, Record<string, string>>>(() => ({
    [firstTarget]: loadDraft(firstTarget),
  }))
  const [copied, setCopied] = useState(false)
  const draft = drafts[target] ?? {}

  const enFlat = useMemo<FlatDict>(() => flattenDictionary(DICTIONARIES.en), [])
  const flats = useMemo<Record<string, FlatDict>>(() => {
    const out: Record<string, FlatDict> = {}
    for (const { code } of TARGET_LOCALES) out[code] = flattenDictionary(DICTIONARIES[code])
    return out
  }, [])

  const stats = useMemo(
    () =>
      TARGET_LOCALES.map(({ code, label }) => ({
        code,
        label,
        ...computeCompletion(enFlat, flats[code], drafts[code] ?? {}),
      })),
    [enFlat, flats, drafts],
  )

  const active = computeCompletion(enFlat, flats[target], draft)

  const selectTarget = useCallback((next: Locale) => {
    setDrafts((prev) => (prev[next] ? prev : { ...prev, [next]: loadDraft(next) }))
    setTargetState(next)
    setCopied(false)
  }, [])

  const onChange = useCallback(
    (key: string, value: string) => {
      setDrafts((prev) => {
        const cur = { ...(prev[target] ?? {}) }
        // Keep the draft a clean delta: a value edited back to the locale's
        // current translation drops out, so the export carries only changes.
        if (value === '' || value === flats[target]?.[key]) delete cur[key]
        else cur[key] = value
        saveDraft(target, cur)
        return { ...prev, [target]: cur }
      })
      setCopied(false)
    },
    [target, flats],
  )

  const copy = useCallback(async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
    } catch {
      setCopied(false)
    }
  }, [])

  return (
    <div className="page container workshop">
      <header className="workshop__head">
        <h1>{t.workshop.title}</h1>
        <p className="workshop__sub">{t.workshop.subtitle}</p>
      </header>

      <section className="workshop__locales" aria-labelledby="workshop-locales-h">
        <h2 id="workshop-locales-h">{t.workshop.localesHeading}</h2>
        <ul className="workshop__locale-list">
          {stats.map((s) => (
            <li key={s.code} className="workshop__locale-row">
              <span className="workshop__locale-label">{s.label}</span>
              <div
                className="workshop__bar"
                role="progressbar"
                aria-valuenow={s.pct}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`${s.label}: ${t.workshop.completion(s.translated, s.total)}`}
              >
                <div className="workshop__bar-fill" style={{ width: `${s.pct}%` }} />
              </div>
              <span className="workshop__locale-count">
                {t.workshop.completion(s.translated, s.total)}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="workshop__editor" aria-labelledby="workshop-editor-h">
        <div className="workshop__editor-head">
          <h2 id="workshop-editor-h">{t.workshop.editorHeading}</h2>
          <label className="workshop__select">
            {t.workshop.selectLocale}
            <select value={target} onChange={(e) => selectTarget(e.target.value as Locale)}>
              {TARGET_LOCALES.map(({ code, label }) => (
                <option key={code} value={code}>
                  {label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <p className="workshop__count">
          {t.workshop.showingCount(active.total, active.untranslated.length)}
        </p>

        {active.total === 0 ? (
          <p className="workshop__done">{t.workshop.allDone}</p>
        ) : (
          <table className="workshop__table">
            <caption>{t.workshop.tableCaption}</caption>
            <thead>
              <tr>
                <th scope="col">{t.workshop.colKey}</th>
                <th scope="col">{t.workshop.colReference}</th>
                <th scope="col">{t.workshop.colDraft}</th>
              </tr>
            </thead>
            <tbody>
              {Object.keys(enFlat)
                .sort()
                .map((key) => {
                  const current = draft[key] ?? flats[target]?.[key] ?? ''
                  const untranslated = current === '' || current === enFlat[key]
                  return (
                    <tr key={key} className={untranslated ? 'workshop__row--untranslated' : undefined}>
                      <td className="workshop__key">
                        {key}
                        {untranslated && (
                          <>
                            {' '}
                            <span className="workshop__untranslated-badge">
                              {t.workshop.untranslatedBadge}
                            </span>
                          </>
                        )}
                      </td>
                      <td>{enFlat[key]}</td>
                      <td>
                        <input
                          className="workshop__input"
                          type="text"
                          value={current}
                          aria-label={t.workshop.draftInputLabel(key)}
                          onChange={(e) => onChange(key, e.target.value)}
                        />
                      </td>
                    </tr>
                  )
                })}
            </tbody>
          </table>
        )}
      </section>

      <section className="workshop__export" aria-labelledby="workshop-export-h">
        <h2 id="workshop-export-h">{t.workshop.exportHeading}</h2>
        <div className="workshop__actions">
          <button type="button" onClick={() => copy(serializeDraftAsTs(target, draft))}>
            {t.workshop.copyTs}
          </button>
          <button type="button" onClick={() => copy(serializeDraftAsJson(draft))}>
            {t.workshop.copyJson}
          </button>
          {copied && (
            <span className="workshop__copied" role="status">
              {t.workshop.copied}
            </span>
          )}
        </div>
      </section>
    </div>
  )
}

export default LanguageWorkshop
