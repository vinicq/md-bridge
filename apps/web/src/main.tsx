import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider, createBrowserRouter } from 'react-router-dom'
import App from './App'
import { I18nProvider } from './i18n'
import { ThemeProvider } from './theme'
import { CONVERTER_PAGES } from './lib/converterRoutes'
import { About } from './pages/About'
import { Home } from './pages/Home'
import { LanguageWorkshop } from './pages/LanguageWorkshop'
import { Preferences } from './pages/Preferences'
import { Themes } from './pages/Themes'
import { applyPrefsToDocument, readPrefs } from './lib/prefs'

// Apply the accent variable and reduce-motion flag once at boot, before first
// paint, so they hold app-wide and not only while the preferences page is open.
applyPrefsToDocument(readPrefs())

// Converter routes come from the shared CONVERTER_PAGES map so the router and the
// format hub never disagree about which pairs have a page (#237).
const converterRoutes = Object.entries(CONVERTER_PAGES).map(([slug, Component]) => ({
  path: `convert/${slug}`,
  Component,
}))

const router = createBrowserRouter([
  {
    path: '/',
    Component: App,
    children: [
      { index: true, Component: Home },
      ...converterRoutes,
      { path: 'about', Component: About },
      { path: 'preferences', Component: Preferences },
      { path: 'themes', Component: Themes },
      { path: 'contribute/i18n', Component: LanguageWorkshop },
    ],
  },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <I18nProvider>
        <RouterProvider router={router} />
      </I18nProvider>
    </ThemeProvider>
  </StrictMode>,
)
