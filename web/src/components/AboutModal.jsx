export default function AboutModal({ onClose }) {
  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.6)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
        zIndex: 100,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--bg-panel)',
          border: '1px solid var(--border)',
          borderRadius: 6,
          padding: '1.5rem',
          maxWidth: '640px',
          width: '100%',
          maxHeight: '90vh',
          overflowY: 'auto',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.75rem' }}>
          <strong style={{ color: 'var(--accent)' }}>▣ Living Runbook Generator</strong>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', fontSize: '1rem' }}
          >
            ✕
          </button>
        </div>
        <p style={{ color: 'var(--text-dim)', marginTop: 0 }}>
          Submit a ticket and watch a runbook update live — this is the same
          pipeline you're using right now, recorded end to end.
        </p>
        <img
          src="/demo.gif"
          alt="Demo: submitting a ticket and watching the runbook update live"
          style={{ width: '100%', borderRadius: 4, border: '1px solid var(--border)' }}
        />
        <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem', marginBottom: 0 }}>
          Source & docs:{' '}
          <a href="https://github.com/superdae-cloud/living-runbook-generator" target="_blank" rel="noreferrer">
            github.com/superdae-cloud/living-runbook-generator
          </a>
        </p>
      </div>
    </div>
  )
}
