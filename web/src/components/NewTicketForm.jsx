import { useState } from 'react'
import { api } from '../api'

const inputStyle = {
  width: '100%',
  background: 'var(--bg)',
  border: '1px solid var(--border)',
  borderRadius: 4,
  color: 'var(--text)',
  padding: '0.5rem',
  marginTop: '0.25rem',
}

const todayIso = () => new Date().toISOString().slice(0, 10)

export default function NewTicketForm({ onCreated, onCancel }) {
  const [form, setForm] = useState({
    date: todayIso(),
    device: '',
    tags: '',
    symptoms: '',
    diagnostics: '',
    root_cause: '',
    resolution: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const result = await api.createTicket({
        date: form.date,
        device: form.device,
        tags: form.tags
          .split(',')
          .map((t) => t.trim().toLowerCase())
          .filter(Boolean),
        symptoms: form.symptoms,
        diagnostics: form.diagnostics,
        root_cause: form.root_cause,
        resolution: form.resolution,
      })
      onCreated(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: '640px' }}>
      <h2 style={{ marginTop: 0 }}>New incident ticket</h2>
      <p style={{ color: 'var(--text-dim)', marginTop: '-0.5rem' }}>
        Submitting writes a ticket .md file and immediately re-runs the pipeline — watch the runbook list update.
      </p>

      <label>
        Date
        <input type="date" required value={form.date} onChange={set('date')} style={inputStyle} />
      </label>
      <div style={{ height: '0.75rem' }} />

      <label>
        Device
        <input required placeholder="PE5-SEA" value={form.device} onChange={set('device')} style={inputStyle} />
      </label>
      <div style={{ height: '0.75rem' }} />

      <label>
        Tags (comma-separated)
        <input
          placeholder="bgp, cpu, pe-router"
          value={form.tags}
          onChange={set('tags')}
          style={inputStyle}
        />
      </label>
      <div style={{ height: '0.75rem' }} />

      <label>
        Symptoms
        <textarea required rows={3} value={form.symptoms} onChange={set('symptoms')} style={inputStyle} />
      </label>
      <div style={{ height: '0.75rem' }} />

      <label>
        Diagnostics
        <textarea
          rows={3}
          placeholder="- bullet point per diagnostic step"
          value={form.diagnostics}
          onChange={set('diagnostics')}
          style={inputStyle}
        />
      </label>
      <div style={{ height: '0.75rem' }} />

      <label>
        Root cause
        <input value={form.root_cause} onChange={set('root_cause')} style={inputStyle} />
      </label>
      <div style={{ height: '0.75rem' }} />

      <label>
        Resolution
        <textarea
          rows={3}
          placeholder="- bullet point per resolution step"
          value={form.resolution}
          onChange={set('resolution')}
          style={inputStyle}
        />
      </label>

      {error && <p style={{ color: 'var(--danger)' }}>{error}</p>}

      <div style={{ marginTop: '1rem', display: 'flex', gap: '0.75rem' }}>
        <button
          type="submit"
          disabled={submitting}
          style={{
            background: 'var(--accent)',
            color: '#04201d',
            border: 'none',
            borderRadius: 4,
            padding: '0.5rem 1rem',
            fontWeight: 'bold',
          }}
        >
          {submitting ? 'Submitting…' : 'Submit + regenerate'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          style={{
            background: 'transparent',
            color: 'var(--text)',
            border: '1px solid var(--border)',
            borderRadius: 4,
            padding: '0.5rem 1rem',
          }}
        >
          Cancel
        </button>
      </div>
    </form>
  )
}
