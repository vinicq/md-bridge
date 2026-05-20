import { NavLink, Outlet } from 'react-router-dom'
import { LanguageSwitcher } from './components/LanguageSwitcher'
import { ThemeToggle } from './components/ThemeToggle'
import { useTranslation } from './i18n'
import './styles/globals.css'
import './App.css'

export function App() {
  const { t } = useTranslation()
  return (
    <>
      <a className="skip-link" href="#main-content">
        {t.a11y.skipToContent}
      </a>
      <header className="app-header">
        <div className="container app-header__inner">
          <NavLink to="/" className="app-header__brand" end>
            md-bridge
          </NavLink>
          <nav className="app-header__nav" aria-label={t.nav.mainLabel}>
            <NavLink to="/convert/pdf-to-md">{t.nav.pdfToMd}</NavLink>
            <NavLink to="/convert/md-to-pdf">{t.nav.mdToPdf}</NavLink>
            <NavLink to="/about">{t.nav.about}</NavLink>
            <LanguageSwitcher />
            <ThemeToggle />
          </nav>
        </div>
      </header>
      <main id="main-content">
        <Outlet />
      </main>
    </>
  )
}

export default App
