import { Link } from 'react-router-dom'
import { useTranslation } from '../i18n'

// Placeholder for the F2 deep theme library. The picker on /md-to-pdf links
// here via "Browse all themes"; the full catalogue page is a future issue.
export function Themes() {
  const { t } = useTranslation()
  return (
    <div className="page container">
      <header className="page__head">
        <h1>{t.themesPage.title}</h1>
        <p>{t.themesPage.subtitle}</p>
      </header>

      <section className="prose">
        <p>
          <Link to="/convert/md-to-pdf">{t.themesPage.back}</Link>
        </p>
      </section>
    </div>
  )
}
