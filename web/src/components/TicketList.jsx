import Tag from './Tag'

export default function TicketList({ tickets, onOpenTicket }) {
  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Tickets</h2>
      <p style={{ color: 'var(--text-dim)', marginTop: '-0.5rem' }}>
        Raw incident history — the input the pipeline clusters into runbooks.
      </p>
      <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '1rem' }}>
        <thead>
          <tr style={{ textAlign: 'left', color: 'var(--text-dim)', borderBottom: '1px solid var(--border)' }}>
            <th style={{ padding: '0.5rem' }}>ID</th>
            <th style={{ padding: '0.5rem' }}>Date</th>
            <th style={{ padding: '0.5rem' }}>Device</th>
            <th style={{ padding: '0.5rem' }}>Tags</th>
            <th style={{ padding: '0.5rem' }}>Symptoms</th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((t) => (
            <tr
              key={t.id}
              onClick={() => onOpenTicket(t.id)}
              style={{ cursor: 'pointer', borderBottom: '1px solid var(--border)' }}
              onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-panel)')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
            >
              <td style={{ padding: '0.5rem' }}>
                <code>{t.id}</code>
              </td>
              <td style={{ padding: '0.5rem' }}>{t.date}</td>
              <td style={{ padding: '0.5rem' }}>{t.device}</td>
              <td style={{ padding: '0.5rem' }}>
                {t.tags.map((tag) => (
                  <Tag key={tag}>{tag}</Tag>
                ))}
              </td>
              <td style={{ padding: '0.5rem', color: 'var(--text-dim)', maxWidth: '360px' }}>
                {t.symptoms.slice(0, 90)}
                {t.symptoms.length > 90 ? '…' : ''}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
