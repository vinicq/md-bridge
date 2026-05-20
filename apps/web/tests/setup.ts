import '@testing-library/jest-dom/vitest'
import { afterEach, beforeEach } from 'vitest'
import { cleanup } from '@testing-library/react'

beforeEach(() => {
  // Reset theme to light before every test so no stale data-theme leaks
  document.documentElement.setAttribute('data-theme', 'light')
})

afterEach(() => {
  cleanup()
})
