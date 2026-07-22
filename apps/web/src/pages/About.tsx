import { useTranslation } from '../i18n'

export function About() {
  const { t } = useTranslation()
  return (
    <div className="page container">
      <header className="page__head">
        <h1>{t.about.title}</h1>
      </header>

      <section className="prose">
        <p>{t.about.intro}</p>

        <h2>{t.about.how.title}</h2>
        <p>{t.about.how.p1}</p>
        <p>{t.about.how.p2}</p>

        <h2>{t.about.limits.title}</h2>
        <ul>
          {t.about.limits.items.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>

        <h2>{t.about.privacy.title}</h2>
        <p>{t.about.privacy.body}</p>

        <h2>{t.about.more.title}</h2>
        <p>{t.about.more.body}</p>
      </section>
    </div>
  )
}
