import { useEffect, useState } from 'react'
import { forceCenter, forceCollide, forceLink, forceManyBody, forceSimulation } from 'd3-force'
import { api } from '../api'

const CLUSTER_COLORS = [
  '#4fd1c5',
  '#f0a020',
  '#f85149',
  '#a78bfa',
  '#60a5fa',
  '#34d399',
  '#fb923c',
  '#f472b6',
]

const WIDTH = 800
const HEIGHT = 520

function colorForCluster(clusterKey, order) {
  const idx = order.indexOf(clusterKey)
  return CLUSTER_COLORS[idx % CLUSTER_COLORS.length]
}

export default function SimilarityGraph({ onSelectTicket }) {
  const [graph, setGraph] = useState(null)
  const [nodes, setNodes] = useState([])
  const [links, setLinks] = useState([])

  useEffect(() => {
    api.graph().then(setGraph)
  }, [])

  // d3-force runs a physics simulation entirely client-side, over data the
  // API already computed (cosine similarity + cluster assignment) — this
  // just lays the same graph out visually, it doesn't recompute anything.
  useEffect(() => {
    if (!graph) return
    const simNodes = graph.nodes.map((n) => ({ ...n }))
    const simLinks = graph.edges.map((e) => ({ ...e }))

    const sim = forceSimulation(simNodes)
      .force(
        'link',
        forceLink(simLinks)
          .id((d) => d.id)
          .distance((d) => 160 * (1 - d.weight) + 40)
          .strength((d) => d.weight),
      )
      .force('charge', forceManyBody().strength(-220))
      .force('center', forceCenter(WIDTH / 2, HEIGHT / 2))
      .force('collide', forceCollide(28))
      .on('tick', () => {
        setNodes(simNodes.map((n) => ({ ...n })))
        setLinks(simLinks.map((l) => ({ ...l })))
      })

    return () => sim.stop()
  }, [graph])

  if (!graph) return <p style={{ color: 'var(--text-dim)' }}>Loading…</p>

  const clusterOrder = [...new Set(graph.nodes.map((n) => n.cluster))]

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Similarity graph</h2>
      <p style={{ color: 'var(--text-dim)', marginTop: '-0.5rem' }}>
        Each node is a ticket. An edge means cosine similarity ≥ {graph.threshold} (the same threshold the
        clustering uses). Color = the runbook the ticket was assigned to.
      </p>
      <svg
        width="100%"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 8 }}
      >
        {links.map((l, i) => {
          const s = typeof l.source === 'object' ? l.source : nodes.find((n) => n.id === l.source)
          const t = typeof l.target === 'object' ? l.target : nodes.find((n) => n.id === l.target)
          if (!s || !t) return null
          return (
            <line
              key={i}
              x1={s.x}
              y1={s.y}
              x2={t.x}
              y2={t.y}
              stroke="var(--border)"
              strokeWidth={1 + l.weight * 3}
              opacity={0.6}
            />
          )
        })}
        {nodes.map((n) => (
          <g
            key={n.id}
            transform={`translate(${n.x || 0},${n.y || 0})`}
            style={{ cursor: 'pointer' }}
            onClick={() => onSelectTicket(n.id)}
          >
            <circle r={14} fill={colorForCluster(n.cluster, clusterOrder)} stroke="var(--bg)" strokeWidth={2} />
            <text textAnchor="middle" dy={28} fontSize={11} fill="var(--text-dim)">
              {n.device || n.id}
            </text>
          </g>
        ))}
      </svg>
      <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        {clusterOrder.map((c) => (
          <div key={c} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
            <span
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                background: colorForCluster(c, clusterOrder),
                display: 'inline-block',
              }}
            />
            {c}
          </div>
        ))}
      </div>
    </div>
  )
}
