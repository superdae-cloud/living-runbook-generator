import { useEffect } from 'react'

const COLORS = {
  info: 'var(--border)',
  success: 'var(--accent)',
  error: 'var(--danger)',
}

export default function Toast({ message, kind, onDone }) {
  useEffect(() => {
    const t = setTimeout(onDone, 4000)
    return () => clearTimeout(t)
  }, [onDone])

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '1.5rem',
        right: '1.5rem',
        background: 'var(--bg-panel)',
        border: `1px solid ${COLORS[kind] || COLORS.info}`,
        borderLeft: `4px solid ${COLORS[kind] || COLORS.info}`,
        borderRadius: 4,
        padding: '0.75rem 1rem',
        maxWidth: '360px',
        boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
      }}
    >
      {message}
    </div>
  )
}
