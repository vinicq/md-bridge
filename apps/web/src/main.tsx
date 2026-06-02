import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider, createBrowserRouter } from 'react-router-dom'
import App from './App'
import { I18nProvider } from './i18n'
import { ThemeProvider } from './theme'
import { About } from './pages/About'
import { Home } from './pages/Home'
import { LanguageWorkshop } from './pages/LanguageWorkshop'
import { MdToPdf } from './pages/MdToPdf'
import { PdfToMd } from './pages/PdfToMd'

const router = createBrowserRouter([
  {
    path: '/',
    Component: App,
    children: [
      { index: true, Component: Home },
      { path: 'convert/pdf-to-md', Component: PdfToMd },
      { path: 'convert/md-to-pdf', Component: MdToPdf },
      { path: 'about', Component: About },
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
