import { useEffect, useState } from 'react'
import { api } from '../api'
import Tag from './Tag'

export default function RunbookDetail({ slug, onBack }) {
  const [rb, setRb] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    setRb(null)
    setError(null)
    api.getRunbook(slug).then(setRb).catch((err) => setError(err.message))
  }, [slug])

  if (error) return <p style={{ color: 'var(--danger)' }}>{error}</p>
  if (!rb) return <p style={{ color: 'var(--text-dim)' }}>Loading…</p>

  return (
    <div style={{ maxWidth: '860px' }}>
      <a href="#" onClick={(e) => { e.preventDefault(); onBack() }}>
        ← back to runbooks
      </a>
      <h2>{rb.title}</h2>

      <Section title="Symptom signature">
        {rb.signature_terms.map((t) => (
          <Tag key={t}>{t}</Tag>
        ))}
        {rb.devices.length > 0 && (
          <p style={{ color: 'var(--text-dim)' }}>Seen on: {rb.devices.join(', ')}</p>
        )}
      </Section>

      <Section title="Frequency">
        <p>
          {rb.incident_count} incident(s) matched this signature
          <br />
          First seen: {rb.first_seen} · Last seen: {rb.last_seen}
        </p>
      </Section>

      <Section title="Diagnostic steps seen across these incidents">
        <ul>
          {rb.diagnostics.map((line, i) => (
            <li key={i}>{line}</li>
          ))}
        </ul>
      </Section>

      <Section title="Likely root cause(s)">
        <ul>
          {rb.root_causes.map((rc, i) => (
            <li key={i}>
              {rc.count > 1 && <strong>({rc.count}×) </strong>}
              {rc.cause}
            </li>
          ))}
        </ul>
      </Section>

      <Section title="Resolution steps that worked">
        <ul>
          {rb.resolutions.map((line, i) => (
            <li key={i}>{line}</li>
          ))}
        </ul>
      </Section>

      <Section title="Source incidents">
        <ul>
          {rb.source_incidents.map((inc) => (
            <li key={inc.id}>
              <code>{inc.id}</code> ({inc.date}, {inc.device || 'device n/a'}) — <code>{inc.file}</code>
            </li>
          ))}
        </ul>
      </Section>

      <Section title="Manual notes">
        <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>
          Edited directly in <code>runbooks/{rb.slug}.md</code> between the MANUAL NOTES markers — survives
          every regeneration.
        </p>
        <pre
          style={{
            background: 'var(--bg-panel)',
            border: '1px solid var(--border)',
            borderRadius: 6,
            padding: '0.75rem',
            whiteSpace: 'pre-wrap',
          }}
        >
          {rb.manual_notes || '(no notes yet)'}
        </pre>
      </Section>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <section style={{ marginBottom: '1.5rem' }}>
      <h3 style={{ borderBottom: '1px solid var(--border)', paddingBottom: '0.25rem' }}>{title}</h3>
      {children}
    </section>
  )
}
