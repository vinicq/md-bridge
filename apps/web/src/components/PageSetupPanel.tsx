import { useId, type ReactNode } from 'react'
import './PageSetupPanel.css'
import type {
  MarginPreset,
  PageSetupLabels,
  PageSetupValue,
  PageSize,
  RunningContent,
} from './pageSetup'

export interface PageSetupPanelProps {
  labels: PageSetupLabels
  value: PageSetupValue
  onChange: (next: PageSetupValue) => void
  /** Disable every control (e.g. while a conversion runs). */
  disabled?: boolean
  /** Slot for a future Table of Contents toggle (#249 backend dep). Renders nothing today. */
  tocToggle?: ReactNode
}

const PAGE_SIZES: PageSize[] = ['A4', 'Letter', 'Legal']
const SLOTS: (keyof RunningContent)[] = ['left', 'center', 'right']

// A page-setup section for the md->pdf page (#249). Separate from <OptionsPanel/>
// (#59) on purpose: that panel speaks toggle+select over a flat fields[] model,
// while this one is two bands of three text slots, which would force a nested
// kind into OptionsPanel and risk regressing the pdf->md surface. Tokens and
// patterns are reused (focus ring, --c-rule, --r-sm, the disabled rule); the
// component is not.
export function PageSetupPanel({
  labels,
  value,
  onChange,
  disabled = false,
  tocToggle,
}: PageSetupPanelProps) {
  // One helper line per panel, referenced by all six slot inputs so a screen
  // reader announces the token list on focus (design contract §4).
  const tokenHelpId = useId()

  const setBandSlot = (band: 'header' | 'footer', slot: keyof RunningContent, text: string) => {
    onChange({ ...value, [band]: { ...value[band], [slot]: text } })
  }

  const renderBand = (band: 'header' | 'footer', legend: string) => (
    <fieldset className="page-setup__group page-setup__band">
      <legend className="page-setup__sublegend">{legend}</legend>
      <div className="page-setup__slots">
        {SLOTS.map((slot) => (
          <label key={slot} className="page-setup__slot">
            <span className="page-setup__label">{labels.slot[slot]}</span>
            <input
              type="text"
              className="page-setup__input"
              value={value[band][slot]}
              placeholder={labels.slotPlaceholder}
              aria-describedby={tokenHelpId}
              onChange={(e) => setBandSlot(band, slot, e.target.value)}
            />
          </label>
        ))}
      </div>
    </fieldset>
  )

  return (
    <fieldset className="page-setup" disabled={disabled}>
      <legend className="page-setup__legend">{labels.legend}</legend>

      <fieldset className="page-setup__group page-setup__page">
        <legend className="page-setup__sublegend">{labels.page.legend}</legend>
        <div className="page-setup__page-grid">
          <label className="page-setup__field">
            <span className="page-setup__label">{labels.pageSize.label}</span>
            <select
              className="page-setup__select"
              value={value.page_size}
              onChange={(e) => onChange({ ...value, page_size: e.target.value as PageSize })}
            >
              {PAGE_SIZES.map((size) => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>
          </label>

          <label className="page-setup__field">
            <span className="page-setup__label">{labels.margins.label}</span>
            <select
              className="page-setup__select"
              value={value.margins}
              onChange={(e) => onChange({ ...value, margins: e.target.value as MarginPreset })}
            >
              <option value="tight">{labels.margins.tight}</option>
              <option value="normal">{labels.margins.normal}</option>
              <option value="loose">{labels.margins.loose}</option>
            </select>
          </label>
        </div>
      </fieldset>

      <p id={tokenHelpId} className="page-setup__token-help">
        {labels.tokenHelp}
      </p>

      {renderBand('header', labels.header.legend)}
      {renderBand('footer', labels.footer.legend)}

      {tocToggle}
    </fieldset>
  )
}
