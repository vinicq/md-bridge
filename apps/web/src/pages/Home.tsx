import { Link } from 'react-router-dom'
import { Card } from '../components/Card'
import { FormatMatrix } from '../components/FormatMatrix'
import { useTranslation } from '../i18n'
import './Home.css'

export function Home() {
  const { t } = useTranslation()
  return (
    <div className="page container">
      <section className="home__hero">
        <h1>{t.home.title}</h1>
        <p className="home__sub">{t.home.subtitle}</p>
      </section>

      <section className="home__cards">
        <Card variant="outline" className="home__card">
          <h2>{t.home.cards.pdfToMd.title}</h2>
          <p>{t.home.cards.pdfToMd.body}</p>
          <Link to="/convert/pdf-to-md" className="home__link">
            {t.home.cards.pdfToMd.cta}
          </Link>
        </Card>

        <Card variant="outline" className="home__card">
          <h2>{t.home.cards.mdToPdf.title}</h2>
          <p>{t.home.cards.mdToPdf.body}</p>
          <Link to="/convert/md-to-pdf" className="home__link">
            {t.home.cards.mdToPdf.cta}
          </Link>
        </Card>
      </section>

      <FormatMatrix />
    </div>
  )
}
