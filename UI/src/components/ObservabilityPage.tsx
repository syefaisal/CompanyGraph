import { useEffect, useState } from 'react'
import { RefreshCw, ExternalLink, AlertTriangle, CheckCircle, Zap, Shield, Clock, DollarSign } from 'lucide-react'
import { api, type Metrics, type LangSmithRun } from '../lib/api'

// ── Helpers ───────────────────────────────────────────────────────────────────

function modelShortName(model: string): string {
  if (model === 'direct') return 'Direct'
  if (model.includes('haiku')) return 'Haiku'
  if (model.includes('sonnet')) return 'Sonnet'
  if (model.includes('opus')) return 'Opus'
  return model
}

function modelColor(model: string): string {
  if (model === 'direct') return 'bg-emerald-500'
  if (model.includes('haiku')) return 'bg-sky-500'
  if (model.includes('sonnet')) return 'bg-violet-500'
  return 'bg-slate-400'
}

function modelBadgeColor(model: string): string {
  if (model === 'direct') return 'bg-emerald-50 text-emerald-700 border-emerald-200'
  if (model.includes('haiku')) return 'bg-sky-50 text-sky-700 border-sky-200'
  if (model.includes('sonnet')) return 'bg-violet-50 text-violet-700 border-violet-200'
  return 'bg-slate-50 text-slate-600 border-slate-200'
}

function runTypeBadge(type: string) {
  const map: Record<string, string> = {
    chain: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    llm: 'bg-violet-50 text-violet-700 border-violet-200',
    tool: 'bg-amber-50 text-amber-700 border-amber-200',
    retriever: 'bg-sky-50 text-sky-700 border-sky-200',
  }
  return map[type] ?? 'bg-slate-50 text-slate-600 border-slate-200'
}

function formatTime(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

// ── Metric card ───────────────────────────────────────────────────────────────

function MetricCard({
  icon, label, value, sub, accent = false,
}: { icon: React.ReactNode; label: string; value: string; sub?: string; accent?: boolean }) {
  return (
    <div className={`rounded-xl border p-4 ${accent ? 'bg-indigo-50 border-indigo-200' : 'bg-white border-slate-200'}`}>
      <div className="flex items-center gap-2 mb-1.5">
        <span className={`${accent ? 'text-indigo-500' : 'text-slate-400'}`}>{icon}</span>
        <span className="text-xs text-slate-500 font-medium">{label}</span>
      </div>
      <p className={`text-2xl font-bold tabular-nums ${accent ? 'text-indigo-700' : 'text-slate-800'}`}>{value}</p>
      {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export function ObservabilityPage() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [lsData, setLsData] = useState<{ enabled: boolean; project?: string; runs: LangSmithRun[]; error?: string } | null>(null)
  const [metricsAge, setMetricsAge] = useState(0)
  const [loading, setLoading] = useState(true)

  async function refresh() {
    setLoading(true)
    try {
      const [m, ls] = await Promise.all([api.metrics(), api.langsmithRuns(15)])
      setMetrics(m)
      setLsData(ls)
      setMetricsAge(0)
    } catch { /* API may not be up yet */ }
    setLoading(false)
  }

  useEffect(() => {
    refresh()
    const poll = setInterval(() => {
      refresh()
    }, 10_000)
    const age = setInterval(() => setMetricsAge((a) => a + 1), 1000)
    return () => { clearInterval(poll); clearInterval(age) }
  }, [])

  const totalRoutes = metrics
    ? Object.values(metrics.model_routes).reduce((a, b) => a + b, 0)
    : 0

  return (
    <div className="h-full overflow-y-auto bg-slate-50">
      <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">

        {/* ── Header ───────────────────────────────────────────────── */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-slate-800">Observability</h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Live session metrics · refreshes every 10 s
              {metricsAge > 0 && <span className="ml-1">· updated {metricsAge}s ago</span>}
            </p>
          </div>
          <button
            onClick={refresh}
            disabled={loading}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 px-3 py-1.5 rounded-lg hover:bg-slate-200 transition-colors"
          >
            <RefreshCw size={11} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>

        {!metrics && !loading && (
          <div className="text-center py-16 text-slate-400 text-sm">
            API not reachable. Make sure the backend is running on port 8000.
          </div>
        )}

        {metrics && (
          <>
            {/* ── Key metric cards ──────────────────────────────────── */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard
                icon={<Zap size={14} />}
                label="Total queries"
                value={String(metrics.queries.total)}
                sub={`${metrics.queries.standard} standard · ${metrics.queries.agent} agent · ${metrics.queries.direct_no_llm} direct`}
                accent
              />
              <MetricCard
                icon={<Clock size={14} />}
                label="Avg latency"
                value={`${metrics.latency.avg_ms.toLocaleString()} ms`}
                sub={`${(metrics.latency.total_ms / 1000).toFixed(1)}s total`}
              />
              <MetricCard
                icon={<DollarSign size={14} />}
                label="Session cost"
                value={`$${metrics.cost_usd.toFixed(4)}`}
                sub={`${((metrics.tokens.cache_hit_rate) * 100).toFixed(0)}% cache hit rate`}
              />
              <MetricCard
                icon={<Shield size={14} />}
                label="Safety events"
                value={String(metrics.safety_events + metrics.output_safety_events)}
                sub={`${metrics.safety_events} input · ${metrics.output_safety_events} output`}
              />
            </div>

            {/* ── Budget status ─────────────────────────────────────── */}
            {metrics.budget && (
              <div className={`rounded-xl border px-4 py-3 flex items-center gap-3 ${
                metrics.budget.exceeded
                  ? 'bg-amber-50 border-amber-300'
                  : 'bg-white border-slate-200'
              }`}>
                {metrics.budget.exceeded
                  ? <AlertTriangle size={15} className="text-amber-500 shrink-0" />
                  : <CheckCircle size={15} className="text-emerald-500 shrink-0" />}
                <div className="flex-1 min-w-0">
                  <p className={`text-xs font-semibold ${metrics.budget.exceeded ? 'text-amber-700' : 'text-slate-700'}`}>
                    {metrics.budget.exceeded ? 'Budget limit reached' : 'Within budget'}
                  </p>
                  <p className="text-xs text-slate-500 truncate">{metrics.budget.note}</p>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-xs font-mono text-slate-600">
                    ${metrics.budget.running_cost_usd.toFixed(4)} / ${metrics.budget.limit_usd.toFixed(2)}
                  </p>
                  {/* Progress bar */}
                  <div className="w-32 h-1.5 bg-slate-200 rounded-full mt-1 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${metrics.budget.exceeded ? 'bg-amber-500' : 'bg-emerald-500'}`}
                      style={{ width: `${Math.min((metrics.budget.running_cost_usd / Math.max(metrics.budget.limit_usd, 0.001)) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* ── Model Routing Strategy ────────────────────────────── */}
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
              <div className="px-5 py-3.5 border-b border-slate-100">
                <h2 className="text-sm font-semibold text-slate-700">Model Selection Strategy</h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Three-tier routing: Direct (no LLM) → Haiku (simple lookups) → Sonnet (complex reasoning)
                </p>
              </div>
              <div className="px-5 py-4 space-y-3">
                {totalRoutes === 0 ? (
                  <p className="text-xs text-slate-400 py-2">No queries yet this session.</p>
                ) : (
                  Object.entries(metrics.model_routes).map(([model, count]) => {
                    const pct = totalRoutes > 0 ? (count / totalRoutes) * 100 : 0
                    const label = modelShortName(model)
                    return (
                      <div key={model} className="space-y-1">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${modelBadgeColor(model)}`}>
                              {label}
                            </span>
                            <span className="text-xs text-slate-500 font-mono">{model}</span>
                          </div>
                          <span className="text-xs text-slate-600 font-semibold tabular-nums">
                            {count} ({pct.toFixed(0)}%)
                          </span>
                        </div>
                        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${modelColor(model)}`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <p className="text-[10px] text-slate-400">
                          {label === 'Direct' && 'List/count queries answered from Neo4j — zero LLM cost'}
                          {label === 'Haiku' && 'Simple entity lookups — fast and low cost'}
                          {label === 'Sonnet' && 'Complex multi-hop reasoning — impact, compliance, path-finding'}
                        </p>
                      </div>
                    )
                  })
                )}
              </div>

              {/* Token breakdown */}
              <div className="border-t border-slate-100 px-5 py-3.5 grid grid-cols-3 gap-4 bg-slate-50/50">
                <div>
                  <p className="text-xs text-slate-400">Input tokens</p>
                  <p className="text-sm font-semibold text-slate-700 tabular-nums">{metrics.tokens.input.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400">Cached tokens</p>
                  <p className="text-sm font-semibold text-emerald-600 tabular-nums">
                    {metrics.tokens.cached.toLocaleString()}
                    <span className="text-xs text-slate-400 font-normal ml-1">
                      ({(metrics.tokens.cache_hit_rate * 100).toFixed(0)}%)
                    </span>
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-400">Output tokens</p>
                  <p className="text-sm font-semibold text-slate-700 tabular-nums">{metrics.tokens.output.toLocaleString()}</p>
                </div>
              </div>
            </div>

            {/* ── LangSmith Trace Feed ──────────────────────────────── */}
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
              <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-semibold text-slate-700">LangSmith Traces</h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {lsData?.enabled
                      ? `Project: ${lsData.project ?? '—'} · last ${lsData.runs.length} runs`
                      : 'Set LANGSMITH_API_KEY + LANGSMITH_TRACING_V2=true to enable'}
                  </p>
                </div>
                {lsData?.enabled && lsData.project && (
                  <a
                    href={`https://smith.langchain.com`}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 transition-colors"
                  >
                    Open LangSmith
                    <ExternalLink size={10} />
                  </a>
                )}
              </div>

              {!lsData?.enabled && (
                <div className="px-5 py-6 text-center">
                  <p className="text-xs text-slate-400">Add to <code className="bg-slate-100 px-1 rounded">.env</code>:</p>
                  <pre className="text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded-lg px-4 py-2 mt-2 text-left inline-block">
{`LANGSMITH_API_KEY=your-key
LANGSMITH_PROJECT=cogni-graph
LANGSMITH_TRACING_V2=true`}
                  </pre>
                </div>
              )}

              {lsData?.error && (
                <div className="px-5 py-4 text-xs text-red-600 bg-red-50">
                  LangSmith error: {lsData.error}
                </div>
              )}

              {lsData?.enabled && !lsData.error && lsData.runs.length === 0 && (
                <div className="px-5 py-6 text-center text-xs text-slate-400">
                  No runs yet. Send a query to generate the first trace.
                </div>
              )}

              {lsData?.enabled && lsData.runs.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-slate-100 bg-slate-50/60">
                        <th className="text-left px-5 py-2.5 text-slate-500 font-medium">Run</th>
                        <th className="text-left px-3 py-2.5 text-slate-500 font-medium">Type</th>
                        <th className="text-left px-3 py-2.5 text-slate-500 font-medium">Status</th>
                        <th className="text-right px-3 py-2.5 text-slate-500 font-medium">Latency</th>
                        <th className="text-right px-3 py-2.5 text-slate-500 font-medium">Tokens in</th>
                        <th className="text-right px-5 py-2.5 text-slate-500 font-medium">Tokens out</th>
                      </tr>
                    </thead>
                    <tbody>
                      {lsData.runs.map((run, i) => (
                        <tr
                          key={run.id}
                          className={`border-b border-slate-50 hover:bg-slate-50/60 transition-colors ${i % 2 === 0 ? '' : 'bg-slate-50/30'}`}
                        >
                          <td className="px-5 py-2.5 font-medium text-slate-700 max-w-[220px] truncate">
                            {run.name || '—'}
                            {run.start_time && (
                              <span className="ml-2 text-slate-400 font-normal">{formatTime(run.start_time)}</span>
                            )}
                          </td>
                          <td className="px-3 py-2.5">
                            <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium border ${runTypeBadge(run.run_type)}`}>
                              {run.run_type}
                            </span>
                          </td>
                          <td className="px-3 py-2.5">
                            <span className={`inline-flex items-center gap-1 text-[10px] font-medium ${
                              run.status === 'success' ? 'text-emerald-600' :
                              run.status === 'error' ? 'text-red-600' : 'text-slate-500'
                            }`}>
                              <span className={`w-1.5 h-1.5 rounded-full ${
                                run.status === 'success' ? 'bg-emerald-500' :
                                run.status === 'error' ? 'bg-red-500' : 'bg-slate-400'
                              }`} />
                              {run.status}
                            </span>
                          </td>
                          <td className="px-3 py-2.5 text-right tabular-nums text-slate-600">
                            {run.latency_s != null ? `${run.latency_s}s` : '—'}
                          </td>
                          <td className="px-3 py-2.5 text-right tabular-nums text-slate-500">
                            {run.input_tokens != null ? run.input_tokens.toLocaleString() : '—'}
                          </td>
                          <td className="px-5 py-2.5 text-right tabular-nums text-slate-500">
                            {run.output_tokens != null ? run.output_tokens.toLocaleString() : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
