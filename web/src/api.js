const BASE = '/api'

async function request(path, options) {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `${res.status} ${res.statusText}`)
  }
  return res.json()
}

export const api = {
  listRunbooks: () => request('/runbooks'),
  getRunbook: (slug) => request(`/runbooks/${encodeURIComponent(slug)}`),
  listTickets: () => request('/tickets'),
  getTicket: (id) => request(`/tickets/${encodeURIComponent(id)}`),
  createTicket: (payload) =>
    request('/tickets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  regenerate: (threshold, synthesize) => {
    const params = new URLSearchParams()
    if (threshold != null) params.set('threshold', threshold)
    if (synthesize != null) params.set('synthesize', synthesize)
    const qs = params.toString()
    return request(`/regenerate${qs ? `?${qs}` : ''}`, { method: 'POST' })
  },
  graph: (threshold) => request(`/graph${threshold != null ? `?threshold=${threshold}` : ''}`),
  search: (q) => request(`/search?q=${encodeURIComponent(q)}`),
  status: () => request('/status'),
}
