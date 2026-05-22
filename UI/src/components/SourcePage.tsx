import { useQuery } from '@tanstack/react-query'
import { FileText, Sparkles, Share2, ArrowRight, ChevronRight } from 'lucide-react'
import { api } from '../lib/api'
import { NODE_COLORS, NODE_LABELS } from '../lib/colors'
import type { NodeLabel } from '../types'

interface NodeEntry {
  name: string
  label: NodeLabel
}

// Apply entity name highlighting within a plain-text string
function applyHighlight(text: string, nodes: NodeEntry[]): React.ReactNode[] {
  if (!text || nodes.length === 0) return [text]
  // Longest name first to prevent partial matches
  const sorted = [...nodes].sort((a, b) => b.name.length - a.name.length)
  const escaped = sorted.map(n => n.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  const pattern = new RegExp(`(${escaped.join('|')})`, 'g')
  return text.split(pattern).flatMap<React.ReactNode>((part, i) => {
    if (!part) return []
    const node = sorted.find(n => n.name === part)
    if (node) {
      const c = NODE_COLORS[node.label]
      return [(
        <span
          key={i}
          title={`${node.label}: ${node.name}`}
          className="rounded px-0.5 cursor-default whitespace-nowrap"
          style={{ backgroundColor: `${c}18`, color: c, fontWeight: 500, borderBottom: `1px dashed ${c}55` }}
        >
          {part}
        </span>
      )]
    }
    return [part]
  })
}

// Render one line of markdown with bold + entity highlighting
function renderLine(line: string, nodes: NodeEntry[]): React.ReactNode[] {
  return line.split(/(\*\*[^*]+\*\*)/g).flatMap<React.ReactNode>((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      const inner = part.slice(2, -2)
      return [(
        <strong key={i} className="font-semibold text-slate-900">
          {applyHighlight(inner, nodes)}
        </strong>
      )]
    }
    return applyHighlight(part, nodes)
  })
}

export function SourcePage() {
  const { data: graph } = useQuery({
    queryKey: ['graph'],
    queryFn: api.fullGraph,
    staleTime: 60_000,
  })

  const { data: briefText, isLoading, isError } = useQuery({
    queryKey: ['brief'],
    queryFn: () => fetch('/api/brief').then(r => {
      if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
      return r.text()
    }),
    staleTime: Infinity,
  })

  const nodes: NodeEntry[] = (graph?.nodes ?? [])
    .map(n => ({ name: n.name ?? '', label: n.label }))
    .filter(n => n.name)

  const relCount = graph?.relationships.length ?? 0

  const counts = NODE_LABELS.map(label => ({
    label,
    count: nodes.filter(n => n.label === label).length,
  }))

  return (
    <div className="h-full overflow-y-auto bg-slate-50">
      <div className="max-w-3xl mx-auto px-6 py-8 space-y-5">

        {/* ── Pipeline banner ─────────────────────────────────────── */}
        <div className="bg-white border border-slate-200 rounded-2xl shadow-card p-5">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-4">
            Ingestion Pipeline
          </p>

          <div className="flex items-stretch gap-2">

            {/* Step 1 */}
            <div className="flex-1 bg-slate-50 border border-slate-200 rounded-xl p-3.5">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-7 h-7 rounded-lg bg-white border border-slate-200 shadow-card flex items-center justify-center shrink-0">
                  <FileText size={13} className="text-slate-500" />
                </div>
                <span className="text-xs font-semibold text-slate-700">Source Document</span>
              </div>
              <p className="text-[11px] font-mono text-slate-500 leading-snug">nexus_corp_brief.md</p>
              <p className="text-[11px] text-slate-400 mt-0.5 leading-snug">Natural-language company brief</p>
            </div>

            {/* Arrow 1 */}
            <div className="flex flex-col items-center justify-center gap-0.5 px-0.5 shrink-0">
              <ArrowRight size={16} className="text-slate-300" />
              <span className="text-[10px] text-slate-400 font-mono">tool_choice</span>
            </div>

            {/* Step 2 */}
            <div className="flex-1 bg-indigo-50 border border-indigo-200 rounded-xl p-3.5">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-7 h-7 rounded-lg bg-indigo-100 flex items-center justify-center shrink-0">
                  <Sparkles size={13} className="text-indigo-600" />
                </div>
                <span className="text-xs font-semibold text-indigo-700">Claude Opus</span>
              </div>
              <p className="text-[11px] text-indigo-500 leading-snug">Entity + relationship</p>
              <p className="text-[11px] text-indigo-400 mt-0.5 leading-snug">extraction via tool use</p>
            </div>

            {/* Arrow 2 */}
            <div className="flex flex-col items-center justify-center gap-0.5 px-0.5 shrink-0">
              <ArrowRight size={16} className="text-slate-300" />
              <span className="text-[10px] text-slate-400 font-mono">MERGE</span>
            </div>

            {/* Step 3 */}
            <div className="flex-1 bg-emerald-50 border border-emerald-200 rounded-xl p-3.5">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-7 h-7 rounded-lg bg-emerald-100 flex items-center justify-center shrink-0">
                  <Share2 size={13} className="text-emerald-600" />
                </div>
                <span className="text-xs font-semibold text-emerald-700">Neo4j Graph</span>
              </div>
              <p className="text-[11px] text-emerald-600 font-semibold leading-snug">
                {nodes.length} nodes · {relCount} rels
              </p>
              <p className="text-[11px] text-emerald-400 mt-0.5 leading-snug">UI · API · MCP</p>
            </div>
          </div>

          {/* Entity type counts */}
          <div className="mt-4 flex gap-2 flex-wrap">
            {counts.map(({ label, count }) => {
              const c = NODE_COLORS[label]
              return (
                <div
                  key={label}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-medium border"
                  style={{ backgroundColor: `${c}10`, borderColor: `${c}35`, color: c }}
                >
                  <span className="font-bold tabular-nums">{count}</span>
                  <span className="opacity-80">{count === 1 ? label : `${label}s`}</span>
                </div>
              )
            })}
          </div>
        </div>

        {/* ── Highlight legend ─────────────────────────────────────── */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <span className="text-xs text-slate-400 shrink-0">Entity highlights:</span>
          {NODE_LABELS.map(label => {
            const c = NODE_COLORS[label]
            return (
              <span
                key={label}
                className="text-xs px-2 py-0.5 rounded font-medium"
                style={{ backgroundColor: `${c}18`, color: c, borderBottom: `1px dashed ${c}55` }}
              >
                {label}
              </span>
            )
          })}
        </div>

        {/* ── Document viewer ──────────────────────────────────────── */}
        <div className="bg-white border border-slate-200 rounded-2xl shadow-card overflow-hidden">

          {/* File header */}
          <div className="flex items-center gap-2 px-5 py-3 border-b border-slate-100 bg-slate-50">
            <FileText size={12} className="text-slate-400" />
            <span className="text-xs font-mono text-slate-500">nexus_corp_brief.md</span>
          </div>

          {isLoading ? (
            <div className="p-10 flex items-center justify-center">
              <div className="relative w-6 h-6">
                <div className="absolute inset-0 rounded-full border border-slate-200" />
                <div className="absolute inset-0 rounded-full border border-t-indigo-500 animate-spin" />
              </div>
            </div>
          ) : isError ? (
            <div className="p-8 text-center">
              <p className="text-sm text-red-500 font-medium mb-1">Could not load brief</p>
              <p className="text-xs text-slate-400">Restart the backend — the /brief endpoint was added after the process started.</p>
            </div>
          ) : (
            <div className="px-6 py-5">
              {(briefText ?? '').split('\n').map((line, i) => {
                // Doc title
                if (line.startsWith('# ')) {
                  return (
                    <h1 key={i} className="text-base font-bold text-slate-900 mb-0.5">
                      {line.slice(2)}
                    </h1>
                  )
                }
                // Section heading
                if (line.startsWith('## ')) {
                  return (
                    <h2 key={i} className="text-xs font-semibold text-slate-500 uppercase tracking-widest mt-6 mb-2.5 pb-1.5 border-b border-slate-100">
                      {line.slice(3)}
                    </h2>
                  )
                }
                // Italic metadata (e.g. *Internal document*)
                if (/^\*[^*].*\*$/.test(line)) {
                  return <p key={i} className="text-xs text-slate-400 italic mb-3">{line.slice(1, -1)}</p>
                }
                // Divider
                if (line.startsWith('---')) {
                  return <div key={i} className="h-1" />
                }
                // Empty line
                if (line.trim() === '') {
                  return <div key={i} className="h-2" />
                }
                // Regular paragraph
                return (
                  <p key={i} className="text-sm leading-relaxed text-slate-600">
                    {renderLine(line, nodes)}
                  </p>
                )
              })}
            </div>
          )}
        </div>

        {/* ── CLI hint ─────────────────────────────────────────────── */}
        <div className="flex items-center gap-3 bg-slate-800 rounded-xl px-4 py-3">
          <ChevronRight size={12} className="text-slate-500 shrink-0" />
          <code className="text-xs text-emerald-400">python doc_to_graph.py --dry-run</code>
          <span className="text-xs text-slate-500 hidden sm:block">
            — preview extracted JSON without writing to Neo4j
          </span>
        </div>

      </div>
    </div>
  )
}
