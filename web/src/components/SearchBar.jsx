import { useEffect, useRef, useState } from 'react'
import { api } from '../api'

export default function SearchBar({ onSelectRunbook, onSelectTicket }) {
  const [q, setQ] = useState('')
  const [results, setResults] = useState(null)
  const [open, setOpen] = useState(false)
  const boxRef = useRef(null)

  useEffect(() => {
    if (!q.trim()) {
      setResults(null)
      return
    }
    const handle = setTimeout(() => {
      api.search(q).then((r) => {
        setResults(r)
        setOpen(true)
      })
    }, 200)
    return () => clearTimeout(handle)
  }, [q])

  useEffect(() => {
    const onClickOutside = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  const pick = (fn, arg) => {
    fn(arg)
    setQ('')
    setResults(null)
    setOpen(false)
  }

  const hasResults = results && (results.runbooks.length > 0 || results.tickets.length > 0)

  return (
    <div ref={boxRef} style={{ position: 'relative' }}>
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        onFocus={() => q && setOpen(true)}
        placeholder="Search runbooks and tickets…"
        style={{
          width: '100%',
          background: 'var(--bg)',
          border: '1px solid var(--border)',
          borderRadius: 4,
          color: 'var(--text)',
          padding: '0.4rem 0.6rem',
        }}
      />
      {open && results && (
        <div
          style={{
            position: 'absolute',
            top: '110%',
            left: 0,
            right: 0,
            background: 'var(--bg-panel)',
            border: '1px solid var(--border)',
            borderRadius: 6,
            zIndex: 10,
            maxHeight: '360px',
            overflowY: 'auto',
          }}
        >
          {!hasResults && <div style={{ padding: '0.6rem', color: 'var(--text-dim)' }}>No matches</div>}
          {results.runbooks.length > 0 && (
            <div>
              <div style={{ padding: '0.4rem 0.6rem', color: 'var(--text-dim)', fontSize: '0.75rem' }}>
                RUNBOOKS
              </div>
              {results.runbooks.map((rb) => (
                <Row key={rb.slug} onClick={() => pick(onSelectRunbook, rb.slug)}>
                  {rb.title}
                </Row>
              ))}
            </div>
          )}
          {results.tickets.length > 0 && (
            <div>
              <div style={{ padding: '0.4rem 0.6rem', color: 'var(--text-dim)', fontSize: '0.75rem' }}>
                TICKETS
              </div>
              {results.tickets.map((t) => (
                <Row key={t.id} onClick={() => pick(onSelectTicket, t.id)}>
                  <code>{t.id}</code> — {t.device} ({t.date})
                </Row>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function Row({ onClick, children }) {
  return (
    <div
      onClick={onClick}
      style={{ padding: '0.5rem 0.6rem', cursor: 'pointer' }}
      onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-panel-hover)')}
      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
    >
      {children}
    </div>
  )
}
