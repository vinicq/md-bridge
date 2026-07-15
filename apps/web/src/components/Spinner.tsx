import './Spinner.css'

interface SpinnerProps {
  size?: number
  // Required so no caller silently ships the Portuguese default to en/es (#354).
  label: string
}

export function Spinner({ size = 24, label }: SpinnerProps) {
  return (
    <span className="spinner" role="status" aria-label={label} style={{ width: size, height: size }}>
      <svg viewBox="0 0 50 50" width={size} height={size} aria-hidden="true">
        <circle
          cx="25"
          cy="25"
          r="20"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray="80 60"
        />
      </svg>
    </span>
  )
}
