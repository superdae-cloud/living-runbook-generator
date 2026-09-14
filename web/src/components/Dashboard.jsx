import Tag from './Tag'

export default function Dashboard({ runbooks, onOpenRunbook }) {
  if (runbooks.length === 0) {
    return <p style={{ color: 'var(--text-dim)' }}>No runbooks yet — add a ticket to generate the first one.</p>
  }

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Runbooks</h2>
      <p style={{ color: 'var(--text-dim)', marginTop: '-0.5rem' }}>
        Auto-generated from incident history, ranked by how often each symptom signature has occurred.
      </p>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
          gap: '1rem',
          marginTop: '1.5rem',
        }}
      >
        {runbooks.map((rb) => (
          <div
            key={rb.slug}
            onClick={() => onOpenRunbook(rb.slug)}
            style={{
              background: 'var(--bg-panel)',
              border: '1px solid var(--border)',
              borderRadius: 8,
              padding: '1rem',
              cursor: 'pointer',
              transition: 'background 0.15s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-panel-hover)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'var(--bg-panel)')}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
              <h3 style={{ margin: '0 0 0.5rem 0' }}>{rb.title}</h3>
              <span
                style={{
                  background: 'var(--accent-dim)',
                  color: 'var(--accent)',
                  borderRadius: 12,
                  padding: '0.1rem 0.6rem',
                  fontSize: '0.85rem',
                  fontWeight: 'bold',
                }}
              >
                {rb.incident_count}×
              </span>
            </div>
            <div style={{ marginBottom: '0.5rem' }}>
              {rb.signature_terms.slice(0, 5).map((term) => (
                <Tag key={term}>{term}</Tag>
              ))}
            </div>
            <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem', margin: 0 }}>
              {rb.first_seen} → {rb.last_seen}
              {rb.devices.length > 0 && <> · {rb.devices.join(', ')}</>}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
