import { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import Dashboard from './components/Dashboard'
import RunbookDetail from './components/RunbookDetail'
import TicketList from './components/TicketList'
import TicketDetail from './components/TicketDetail'
import NewTicketForm from './components/NewTicketForm'
import SimilarityGraph from './components/SimilarityGraph'
import SearchBar from './components/SearchBar'
import Toast from './components/Toast'
import AboutModal from './components/AboutModal'

// No react-router here on purpose — the whole app is five simple views
// over one dataset, so a tiny {view, param} state machine is enough and
// keeps the dependency list short.
export default function App() {
  const [view, setView] = useState({ name: 'dashboard' })
  const [runbooks, setRunbooks] = useState([])
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState(null)
  const [status, setStatus] = useState(null)
  const [showAbout, setShowAbout] = useState(false)

  const notify = useCallback((message, kind = 'info') => {
    setToast({ message, kind, key: Date.now() })
  }, [])

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const [rb, tk] = await Promise.all([api.listRunbooks(), api.listTickets()])
      setRunbooks(rb)
      setTickets(tk)
    } catch (err) {
      notify(`Failed to load data: ${err.message}`, 'error')
    } finally {
      setLoading(false)
    }
  }, [notify])

  useEffect(() => {
    refresh()
    api.status().then(setStatus).catch(() => {})
  }, [refresh])

  const goDashboard = () => setView({ name: 'dashboard' })
  const goTickets = () => setView({ name: 'tickets' })
  const goGraph = () => setView({ name: 'graph' })
  const goNewTicket = () => setView({ name: 'new-ticket' })
  const goRunbook = (slug) => setView({ name: 'runbook', slug })
  const goTicket = (id) => setView({ name: 'ticket', id })

  const handleRegenerate = async (synthesizeOverride) => {
    notify('Regenerating runbooks…')
    try {
      const result = await api.regenerate(undefined, synthesizeOverride)
      const aiNote = result.synthesize_enabled ? `, ${result.synthesized_count} AI-synthesized` : ''
      notify(
        `Regenerated: ${result.ticket_count} ticket(s) → ${result.cluster_count} runbook(s)${aiNote}`,
        'success',
      )
      setStatus((s) => (s ? { ...s, synthesize_enabled: result.synthesize_enabled } : s))
      await refresh()
    } catch (err) {
      notify(`Regenerate failed: ${err.message}`, 'error')
    }
  }

  const handleToggleSynthesize = async () => {
    if (!status?.llm_configured) {
      notify('AI synthesis needs Anthropic credentials configured on the server — see README.', 'error')
      return
    }
    await handleRegenerate(!status.synthesize_enabled)
  }

  const handleTicketCreated = async (result) => {
    notify(`Created ${result.created} — pipeline re-ran (${result.runbook_count} runbook(s))`, 'success')
    await refresh()
    goDashboard()
  }

  return (
    <div style={{ minHeight: '100%', display: 'flex', flexDirection: 'column' }}>
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '1.5rem',
          padding: '0.75rem 1.5rem',
          borderBottom: '1px solid var(--border)',
          background: 'var(--bg-panel)',
          flexWrap: 'wrap',
        }}
      >
        <strong style={{ cursor: 'pointer', color: 'var(--accent)' }} onClick={goDashboard}>
          ▣ Living Runbook Generator
        </strong>
        <button
          onClick={() => setShowAbout(true)}
          title="What is this?"
          style={{
            background: 'transparent',
            color: 'var(--text-dim)',
            border: '1px solid var(--border)',
            borderRadius: '50%',
            width: '1.75rem',
            height: '1.75rem',
            lineHeight: 1,
            cursor: 'pointer',
          }}
        >
          ℹ
        </button>
        <nav style={{ display: 'flex', gap: '1rem' }}>
          <NavLink active={view.name === 'dashboard'} onClick={goDashboard}>
            Runbooks
          </NavLink>
          <NavLink active={view.name === 'tickets'} onClick={goTickets}>
            Tickets
          </NavLink>
          <NavLink active={view.name === 'graph'} onClick={goGraph}>
            Similarity graph
          </NavLink>
        </nav>
        <div style={{ flex: 1, minWidth: '200px' }}>
          <SearchBar onSelectRunbook={goRunbook} onSelectTicket={goTicket} />
        </div>
        <button
          onClick={goNewTicket}
          style={{
            background: 'var(--accent)',
            color: '#04201d',
            border: 'none',
            borderRadius: 4,
            padding: '0.4rem 0.8rem',
            fontWeight: 'bold',
          }}
        >
          + New ticket
        </button>
        <button
          onClick={() => handleRegenerate()}
          style={{
            background: 'transparent',
            color: 'var(--text)',
            border: '1px solid var(--border)',
            borderRadius: 4,
            padding: '0.4rem 0.8rem',
          }}
        >
          ↻ Regenerate
        </button>
        <button
          onClick={handleToggleSynthesize}
          title={
            status?.llm_configured
              ? `Ask ${status.llm_model} to synthesize one root-cause paragraph per cluster`
              : 'Needs Anthropic credentials configured on the server'
          }
          style={{
            background: status?.synthesize_enabled ? 'var(--accent-dim)' : 'transparent',
            color: status?.synthesize_enabled ? 'var(--accent)' : 'var(--text-dim)',
            border: '1px solid var(--border)',
            borderRadius: 4,
            padding: '0.4rem 0.8rem',
            opacity: status?.llm_configured ? 1 : 0.6,
          }}
        >
          ✨ AI root cause: {status?.synthesize_enabled ? 'On' : 'Off'}
        </button>
      </header>

      <main style={{ flex: 1, padding: '1.5rem' }}>
        {loading && runbooks.length === 0 && tickets.length === 0 ? (
          <p style={{ color: 'var(--text-dim)' }}>Loading…</p>
        ) : view.name === 'dashboard' ? (
          <Dashboard runbooks={runbooks} onOpenRunbook={goRunbook} />
        ) : view.name === 'runbook' ? (
          <RunbookDetail slug={view.slug} onBack={goDashboard} />
        ) : view.name === 'tickets' ? (
          <TicketList tickets={tickets} onOpenTicket={goTicket} />
        ) : view.name === 'ticket' ? (
          <TicketDetail id={view.id} onBack={goTickets} />
        ) : view.name === 'new-ticket' ? (
          <NewTicketForm onCreated={handleTicketCreated} onCancel={goDashboard} />
        ) : view.name === 'graph' ? (
          <SimilarityGraph onSelectTicket={goTicket} />
        ) : null}
      </main>

      {toast && <Toast key={toast.key} message={toast.message} kind={toast.kind} onDone={() => setToast(null)} />}
      {showAbout && <AboutModal onClose={() => setShowAbout(false)} />}
    </div>
  )
}

function NavLink({ active, onClick, children }) {
  return (
    <a
      onClick={(e) => {
        e.preventDefault()
        onClick()
      }}
      href="#"
      style={{
        color: active ? 'var(--accent)' : 'var(--text-dim)',
        fontWeight: active ? 'bold' : 'normal',
      }}
    >
      {children}
    </a>
  )
}
