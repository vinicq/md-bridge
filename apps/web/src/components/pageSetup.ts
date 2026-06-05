// Value types + default for the page-setup panel (#249). Kept out of
// PageSetupPanel.tsx so the component file exports only the component (the
// react-refresh/only-export-components rule allows primitive constants beside a
// component, but not an object literal default).

export type PageSize = 'A4' | 'Letter' | 'Legal'
export type MarginPreset = 'tight' | 'normal' | 'loose'

export interface RunningContent {
  left: string
  center: string
  right: string
}

export interface PageSetupValue {
  page_size: PageSize
  margins: MarginPreset
  header: RunningContent
  footer: RunningContent
}

export interface PageSetupLabels {
  legend: string
  page: { legend: string }
  pageSize: { label: string }
  margins: { label: string; tight: string; normal: string; loose: string }
  header: { legend: string }
  footer: { legend: string }
  slot: { left: string; center: string; right: string }
  tokenHelp: string
  slotPlaceholder: string
}

// Default geometry mirrors the backend's historic A4 / normal box (#243): the
// panel starts where the renderer already was, so an untouched panel reproduces
// the pre-#249 output. Empty slots stay '' (not undefined); the #243 backend
// skips empty bands.
export const DEFAULT_PAGE_SETUP: PageSetupValue = {
  page_size: 'A4',
  margins: 'normal',
  header: { left: '', center: '', right: '' },
  footer: { left: '', center: '', right: '' },
}
