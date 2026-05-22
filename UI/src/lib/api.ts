import type {
  FullGraph,
  GraphNode,
  GraphStats,
  ImpactResult,
  NodeLabel,
  NodeWithConnections,
} from '../types'

const BASE = '/api'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as { detail?: string }).detail ?? `${res.status}`)
  }
  return res.json()
}

async function del<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export const api = {
  health: () => get<{ status: string; stats: GraphStats }>('/'),
  fullGraph: () => get<FullGraph>('/graph'),
  listNodes: (type?: NodeLabel, limit = 200) =>
    get<GraphNode[]>(`/nodes?${type ? `type=${type}&` : ''}limit=${limit}`),
  getNode: (id: string) => get<NodeWithConnections>(`/nodes/${id}`),
  deleteNode: (id: string) => del<{ deleted: string }>(`/nodes/${id}`),
  createNode: (label: NodeLabel, properties: Record<string, unknown>) =>
    post<GraphNode>('/nodes', { label, properties }),
  createRelationship: (
    from_id: string,
    to_id: string,
    rel_type: string,
    properties: Record<string, unknown> = {}
  ) => post('/relationships', { from_id, to_id, rel_type, properties }),
  search: (q: string, type?: NodeLabel) =>
    get<GraphNode[]>(`/search?q=${encodeURIComponent(q)}${type ? `&type=${type}` : ''}`),
  impact: (id: string) => get<ImpactResult>(`/impact/${id}`),
}
