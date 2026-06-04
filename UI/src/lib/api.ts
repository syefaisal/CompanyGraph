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

export interface Metrics {
  prompt_version: string
  queries: { total: number; standard: number; agent: number; direct_no_llm: number }
  latency: { avg_ms: number; total_ms: number }
  tokens: { input: number; cached: number; output: number; cache_hit_rate: number }
  cost_usd: number
  model_routes: Record<string, number>
  cache_hits: number
  errors: number
  safety_events: number
  output_safety_events: number
  budget: { limit_usd: number; running_cost_usd: number; exceeded: boolean; note: string }
}

export interface LangSmithRun {
  id: string
  name: string
  run_type: string
  status: string
  latency_s: number | null
  input_tokens: number | null
  output_tokens: number | null
  start_time: string | null
}

export const api = {
  health: () => get<{ status: string; stats: GraphStats }>('/'),
  fullGraph: () => get<FullGraph>('/graph'),
  metrics: () => get<Metrics>('/metrics'),
  langsmithRuns: (limit = 10) =>
    get<{ enabled: boolean; project?: string; runs: LangSmithRun[]; error?: string }>(
      `/langsmith/runs?limit=${limit}`
    ),
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
  search: (q: string, mode: 'hybrid' | 'keyword' = 'hybrid', type?: NodeLabel) =>
    get<GraphNode[]>(
      `/search?q=${encodeURIComponent(q)}&mode=${mode}${type ? `&type=${type}` : ''}`
    ),
  impact: (id: string) => get<ImpactResult>(`/impact/${id}`),
}
