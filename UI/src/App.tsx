import { useState, useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, RefreshCw, Network, GitMerge, Zap, FileText } from 'lucide-react'
import { api } from './lib/api'
import { GraphCanvas } from './components/GraphCanvas'
import { NodePanel } from './components/NodePanel'
import { SearchBar } from './components/SearchBar'
import { StatsBar } from './components/StatsBar'
import { FilterChips } from './components/FilterChips'
import { AddNodeModal } from './components/AddNodeModal'
import { QueryPage } from './components/QueryPage'
import { SourcePage } from './components/SourcePage'
import type { FGNode, NodeLabel } from './types'

type Tab = 'graph' | 'query' | 'source'

export default function App() {
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('graph')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [focusId, setFocusId] = useState<string | null>(null)
  const [hiddenLabels, setHiddenLabels] = useState<Set<NodeLabel>>(new Set())
  const [showAdd, setShowAdd] = useState(false)

  const { data: graph, isLoading, isError } = useQuery({
    queryKey: ['graph'],
    queryFn: api.fullGraph,
    staleTime: 60_000,
  })

  const { nodes, links } = useMemo(() => {
    if (!graph) return { nodes: [], links: [] }
    const nodes: FGNode[] = graph.nodes.map((n) => ({ id: n.id, label: n.label, name: n.name }))
    const links = graph.relationships.map((r) => ({ source: r.from_id, target: r.to_id, type: r.type }))
    return { nodes, links }
  }, [graph])

  function toggleLabel(label: NodeLabel) {
    setHiddenLabels((prev) => {
      const next = new Set(prev)
      next.has(label) ? next.delete(label) : next.add(label)
      return next
    })
  }

  const visibleCount = nodes.filter((n) => !hiddenLabels.has(n.label)).length

  return (
    <div className="h-screen w-screen bg-graph-bg flex flex-col overflow-hidden">

      {/* ── Header ─────────────────────────────────────────────────── */}
      <header className="flex items-center gap-3 px-5 py-2.5 bg-white border-b border-slate-200 shadow-card shrink-0 z-20">

        {/* Brand */}
        <div className="flex items-center gap-2.5 mr-1 select-none">
          <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center justify-center">
            <Network size={15} className="text-indigo-600" />
          </div>
          <span className="font-semibold text-sm text-brand tracking-tight">CogniGraph</span>
        </div>

        <div className="h-5 w-px bg-slate-200" />

        {/* Tabs */}
        <div className="flex items-center gap-0.5 bg-slate-100 rounded-lg p-1">
          {([['graph', GitMerge, 'Graph'], ['query', Zap, 'Query'], ['source', FileText, 'Source']] as const).map(([id, Icon, label]) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-md transition-all duration-200 ${
                tab === id
                  ? 'bg-white text-indigo-600 shadow-card'
                  : 'text-slate-500 hover:text-slate-700 hover:bg-slate-200/70'
              }`}
            >
              <Icon size={12} />
              {label}
            </button>
          ))}
        </div>

        {tab === 'graph' && <SearchBar onSelect={(node) => { setSelectedId(node.id); setFocusId(node.id) }} />}

        <div className="flex-1" />

        <StatsBar />

        {tab === 'graph' && (
          <>
            <div className="h-5 w-px bg-slate-200" />
            <button
              onClick={() => qc.invalidateQueries({ queryKey: ['graph'] })}
              className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 transition-colors px-2.5 py-1.5 rounded-lg hover:bg-slate-100"
            >
              <RefreshCw size={11} />
              Refresh
            </button>
            <button
              onClick={() => setShowAdd(true)}
              className="flex items-center gap-1.5 text-xs bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1.5 rounded-lg transition-colors font-medium shadow-sm"
            >
              <Plus size={12} />
              Add Node
            </button>
          </>
        )}
      </header>

      {/* ── Query page ─────────────────────────────────────────────── */}
      {tab === 'query' && (
        <div className="flex-1 overflow-hidden">
          <QueryPage />
        </div>
      )}

      {/* ── Source page ────────────────────────────────────────────── */}
      {tab === 'source' && (
        <div className="flex-1 overflow-hidden">
          <SourcePage />
        </div>
      )}

      {/* ── Graph page ─────────────────────────────────────────────── */}
      {tab === 'graph' && (
        <div className="flex-1 flex overflow-hidden relative">
          <div className="flex-1 relative overflow-hidden">

            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center z-10">
                <div className="flex flex-col items-center gap-4 animate-fade-in">
                  <div className="relative w-10 h-10">
                    <div className="absolute inset-0 rounded-full border-2 border-slate-200" />
                    <div className="absolute inset-0 rounded-full border-2 border-t-indigo-500 animate-spin" />
                  </div>
                  <span className="text-slate-400 text-sm">Loading graph…</span>
                </div>
              </div>
            )}

            {isError && (
              <div className="absolute inset-0 flex items-center justify-center z-10">
                <div className="text-center bg-white border border-slate-200 rounded-2xl px-8 py-6 shadow-panel animate-fade-in">
                  <div className="w-10 h-10 bg-red-50 border border-red-200 rounded-xl flex items-center justify-center mx-auto mb-3">
                    <span className="text-red-500 text-lg font-bold">!</span>
                  </div>
                  <p className="text-red-600 text-sm font-medium mb-1">Could not reach the API</p>
                  <p className="text-slate-400 text-xs">Make sure the backend is running on port 8000</p>
                </div>
              </div>
            )}

            {!isLoading && (
              <GraphCanvas
                nodes={nodes}
                links={links}
                selectedId={selectedId}
                focusId={focusId}
                hiddenLabels={hiddenLabels}
                onNodeClick={(node: FGNode) => setSelectedId(node.id === selectedId ? null : node.id)}
                onBackgroundClick={() => setSelectedId(null)}
              />
            )}

            {/* Filter chips */}
            <div className="absolute bottom-4 left-4 z-10 animate-fade-in">
              <div className="glass border border-slate-200 shadow-panel rounded-xl px-3 py-2.5">
                <FilterChips hidden={hiddenLabels} onToggle={toggleLabel} />
              </div>
            </div>

            {/* Node count */}
            {graph && (
              <div className="absolute top-4 right-4 z-10 glass border border-slate-200 shadow-card rounded-lg px-3 py-1.5 text-xs text-slate-500 tabular-nums animate-fade-in">
                {hiddenLabels.size > 0
                  ? <><span className="text-slate-800 font-semibold">{visibleCount}</span> / {nodes.length} nodes</>
                  : <><span className="text-slate-800 font-semibold">{nodes.length}</span> nodes</>}
              </div>
            )}
          </div>

          {/* Side panel */}
          <aside
            className={`shrink-0 border-l border-slate-200 bg-white transition-all duration-300 ease-out overflow-hidden shadow-panel ${
              selectedId ? 'w-80' : 'w-0'
            }`}
          >
            {selectedId && (
              <div className="animate-slide-in-right h-full">
                <NodePanel
                  nodeId={selectedId}
                  onClose={() => setSelectedId(null)}
                  onNavigate={(id) => setSelectedId(id)}
                />
              </div>
            )}
          </aside>
        </div>
      )}

      {showAdd && <AddNodeModal onClose={() => setShowAdd(false)} />}
    </div>
  )
}
