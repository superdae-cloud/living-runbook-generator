export default function Tag({ children }) {
  return (
    <span
      style={{
        display: 'inline-block',
        background: 'var(--bg)',
        border: '1px solid var(--border)',
        color: 'var(--text-dim)',
        borderRadius: 4,
        padding: '0.1rem 0.5rem',
        fontSize: '0.8rem',
        marginRight: '0.35rem',
        marginBottom: '0.35rem',
      }}
    >
      {children}
    </span>
  )
}
