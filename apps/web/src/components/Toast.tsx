import { useCallback, useEffect, useRef } from 'react'

interface ToastProps {
  kind?: 'info' | 'ok' | 'warn'
  message: string
  onDismiss: () => void
  duration?: number
  /** Accessible label for the dismiss button (from the i18n catalog). */
  dismissLabel: string
}

export function Toast({
  kind = 'info',
  message,
  onDismiss,
  duration = 3000,
  dismissLabel,
}: ToastProps) {
  const timerRef = useRef<number | null>(null)
  // Keep the latest onDismiss/duration in refs so the auto-dismiss timer can be
  // armed once on mount without restarting every time the parent passes a new
  // inline handler. Pages pass `onDismiss={() => setToast(null)}`, a fresh
  // identity per render; typing in a textarea used to reset the timer on every
  // keystroke so the toast never closed (#355).
  const onDismissRef = useRef(onDismiss)
  const durationRef = useRef(duration)
  useEffect(() => {
    onDismissRef.current = onDismiss
  }, [onDismiss])
  useEffect(() => {
    durationRef.current = duration
  }, [duration])

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const startTimer = useCallback(() => {
    clearTimer()
    timerRef.current = window.setTimeout(() => onDismissRef.current(), durationRef.current)
  }, [clearTimer])

  // Arm once on mount. startTimer/clearTimer are stable, so a parent re-render
  // no longer re-runs this effect and the countdown survives (#355).
  useEffect(() => {
    startTimer()
    return clearTimer
  }, [startTimer, clearTimer])

  return (
    <div
      className={`toast toast--${kind}`}
      role="status"
      onMouseEnter={clearTimer}
      onMouseLeave={startTimer}
    >
      <span className="toast__message">{message}</span>
      <button
        type="button"
        className="toast__dismiss"
        aria-label={dismissLabel}
        onClick={onDismiss}
        onFocus={clearTimer}
        onBlur={startTimer}
      >
        <span aria-hidden="true">×</span>
      </button>
    </div>
  )
}
