import { useEffect, useState } from 'react'
import { api } from '../api'
import Tag from './Tag'

export default function TicketDetail({ id, onBack }) {
  const [ticket, setTicket] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    setTicket(null)
    setError(null)
    api.getTicket(id).then(setTicket).catch((err) => setError(err.message))
  }, [id])

  if (error) return <p style={{ color: 'var(--danger)' }}>{error}</p>
  if (!ticket) return <p style={{ color: 'var(--text-dim)' }}>Loading…</p>

  return (
    <div style={{ maxWidth: '720px' }}>
      <a href="#" onClick={(e) => { e.preventDefault(); onBack() }}>
        ← back to tickets
      </a>
      <h2>
        <code>{ticket.id}</code>
      </h2>
      <p style={{ color: 'var(--text-dim)' }}>
        {ticket.date} · {ticket.device} · <code>{ticket.file}</code>
      </p>
      <div>
        {ticket.tags.map((t) => (
          <Tag key={t}>{t}</Tag>
        ))}
      </div>

      <Field title="Symptoms" value={ticket.symptoms} />
      <Field title="Diagnostics" value={ticket.diagnostics} />
      <Field title="Root Cause" value={ticket.root_cause} />
      <Field title="Resolution" value={ticket.resolution} />
    </div>
  )
}

function Field({ title, value }) {
  return (
    <section style={{ marginBottom: '1.25rem' }}>
      <h3 style={{ borderBottom: '1px solid var(--border)', paddingBottom: '0.25rem' }}>{title}</h3>
      <p style={{ whiteSpace: 'pre-wrap' }}>{value || <span style={{ color: 'var(--text-dim)' }}>(none)</span>}</p>
    </section>
  )
}
