import { useCallback, useEffect, useRef } from 'react'

interface ToastProps {
  kind?: 'info' | 'ok' | 'warn'
  message: string
  onDismiss: () => void
  duration?: number
}

export function Toast({ kind = 'info', message, onDismiss, duration = 3000 }: ToastProps) {
  const timerRef = useRef<number | null>(null)

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const startTimer = useCallback(() => {
    clearTimer()
    timerRef.current = window.setTimeout(onDismiss, duration)
  }, [clearTimer, duration, onDismiss])

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
      onFocus={clearTimer}
      onBlur={startTimer}
    >
      {message}
    </div>
  )
}
