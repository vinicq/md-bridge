import { test, expect } from '@playwright/test'

/**
 * WCAG 2.3.3 (Animation from Interactions) + 2.2.2 (Pause, Stop, Hide).
 *
 * A regra global em globals.css zera animation-duration / transition-duration
 * quando o usuario sinaliza prefers-reduced-motion. Componentes que dependem
 * visualmente de movimento continuo (Spinner, .btn__spinner) tem fallback
 * estatico que mantem o elemento visivel via border pontilhada.
 */
test.use({ reducedMotion: 'reduce' })

// `test.use({ reducedMotion })` configura o contexto, mas em algumas versoes
// do Playwright + Chromium o estado nao propaga consistentemente para o
// CSS engine antes do primeiro goto. `page.emulateMedia` por chamada
// garante que o `@media (prefers-reduced-motion: reduce)` case na pagina.
test.beforeEach(async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
})

const NEAR_ZERO_MS = 50

/**
 * Converte a string `animationDuration`/`transitionDuration` do
 * getComputedStyle (ex.: "0.12s", "1e-05s", "0.01ms") para milissegundos.
 * Sem isso, `parseFloat("0.12s") === 0.12` pareceria menor que 50ms.
 */
function toMs(value: string): number {
  const first = value.split(',')[0].trim()
  const num = parseFloat(first)
  if (!Number.isFinite(num)) return 0
  if (first.endsWith('ms')) return num
  if (first.endsWith('s')) return num * 1000
  return num
}

test('page fade-in is suppressed when reduced motion is requested', async ({ page }) => {
  await page.goto('/')

  const animationDuration = await page
    .locator('.page')
    .first()
    .evaluate((el) => getComputedStyle(el).animationDuration)

  expect(toMs(animationDuration)).toBeLessThan(NEAR_ZERO_MS)
})

test('anchor transition-duration collapses with reduced motion', async ({ page }) => {
  await page.goto('/')

  // O seletor `a` no globals.css declara `transition: color var(--t-fast) var(--easing)`.
  // Com a media query ativa, transition-duration deve estar quase em zero.
  const transitionDuration = await page
    .locator('a')
    .first()
    .evaluate((el) => getComputedStyle(el).transitionDuration)

  expect(toMs(transitionDuration)).toBeLessThan(NEAR_ZERO_MS)
})

test('spinner remains visible (dotted ring fallback) under reduced motion', async ({ page }) => {
  // /convert/md-to-pdf importa BatchPanel, que importa Spinner. Sem isso,
  // a CSS de Spinner nao seria carregada (Vite faz code-splitting de CSS
  // por componente) e o seletor `.spinner` nao teria efeito no DOM
  // sintetico que injetamos.
  await page.goto('/convert/md-to-pdf')

  // Injeta um <span class="spinner"> espelhando o markup real de
  // <Spinner />. Evita depender de um estado de loading da UI real,
  // e ainda assim exercita a regra CSS do componente em producao.
  await page.evaluate(() => {
    const el = document.createElement('span')
    el.className = 'spinner'
    el.setAttribute('role', 'status')
    el.setAttribute('aria-label', 'Carregando')
    el.id = 'rm-test-spinner'
    el.style.width = '24px'
    el.style.height = '24px'

    const svgNS = 'http://www.w3.org/2000/svg'
    const svg = document.createElementNS(svgNS, 'svg')
    svg.setAttribute('viewBox', '0 0 50 50')
    svg.setAttribute('width', '24')
    svg.setAttribute('height', '24')
    svg.setAttribute('aria-hidden', 'true')
    const circle = document.createElementNS(svgNS, 'circle')
    circle.setAttribute('cx', '25')
    circle.setAttribute('cy', '25')
    circle.setAttribute('r', '20')
    circle.setAttribute('fill', 'none')
    circle.setAttribute('stroke', 'currentColor')
    svg.appendChild(circle)
    el.appendChild(svg)

    document.body.appendChild(el)
  })

  const spinner = page.locator('#rm-test-spinner')
  await expect(spinner).toBeVisible()

  const box = await spinner.boundingBox()
  expect(box).not.toBeNull()
  expect(box!.width).toBeGreaterThan(0)
  expect(box!.height).toBeGreaterThan(0)

  // O fallback troca o anel rotativo por uma borda pontilhada.
  const borderStyle = await spinner.evaluate((el) => getComputedStyle(el).borderTopStyle)
  expect(borderStyle).toBe('dotted')

  // E o SVG interno fica escondido (display: none) para nao mostrar
  // um arco congelado por tras do anel estatico.
  const svgDisplay = await page
    .locator('#rm-test-spinner svg')
    .evaluate((el) => getComputedStyle(el).display)
  expect(svgDisplay).toBe('none')
})
