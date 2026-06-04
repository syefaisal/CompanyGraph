import { useState, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, X, Sparkles } from 'lucide-react'
import { api } from '../lib/api'
import { NodeBadge } from './NodeBadge'
import { MatchBadge } from './MatchBadge'
import type { GraphNode } from '../types'

type Mode = 'hybrid' | 'keyword'

interface Props {
  onSelect: (node: GraphNode) => void
}

export function SearchBar({ onSelect }: Props) {
  const [q, setQ] = useState('')
  const [mode, setMode] = useState<Mode>('hybrid')
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const active = q.trim().length >= 2
  const { data: results = [], isFetching } = useQuery({
    queryKey: ['search', mode, q],
    queryFn: () => api.search(q, mode),
    enabled: active,
    staleTime: 5_000,
  })

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  function pick(node: GraphNode) {
    setQ('')
    setOpen(false)
    onSelect(node)
  }

  const showPanel = open && active
  const noMatches = showPanel && !isFetching && results.length === 0

  return (
    <div ref={ref} className="relative w-80">
      <div className={`flex items-center gap-2 bg-white border rounded-lg px-3 py-2 transition-all duration-200 ${
        showPanel && results.length > 0 ? 'border-indigo-400 shadow-sm' : 'border-slate-200 hover:border-slate-300'
      }`}>
        <Search size={13} className="text-slate-400 shrink-0" />
        <input
          className="bg-transparent text-sm text-slate-800 placeholder-slate-400 outline-none flex-1 min-w-0"
          placeholder="Search nodes…"
          value={q}
          onChange={(e) => { setQ(e.target.value); setOpen(true) }}
          onFocus={() => setOpen(true)}
        />
        {/* Hybrid | Keyword mode toggle */}
        <div className="flex items-center rounded-md bg-slate-100 p-0.5 shrink-0">
          {(['hybrid', 'keyword'] as Mode[]).map((m) => (
            <button
              key={m}
              onClick={() => { setMode(m); setOpen(true) }}
              title={m === 'hybrid' ? 'BM25 + semantic embeddings (RRF)' : 'Exact substring match'}
              className={`flex items-center gap-1 px-2 py-0.5 text-[11px] font-medium rounded transition-colors ${
                mode === m ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              {m === 'hybrid' && <Sparkles size={10} />}
              {m === 'hybrid' ? 'Hybrid' : 'Keyword'}
            </button>
          ))}
        </div>
        {q && (
          <button
            onClick={() => { setQ(''); setOpen(false) }}
            className="text-slate-300 hover:text-slate-500 transition-colors shrink-0"
          >
            <X size={12} />
          </button>
        )}
      </div>

      {showPanel && (
        <div className="absolute top-full mt-1.5 left-0 right-0 bg-white border border-slate-200 rounded-xl shadow-panel z-50 overflow-hidden animate-fade-in">
          {/* Mode caption — makes the active retrieval strategy visible */}
          <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-100 bg-slate-50/60">
            <span className="flex items-center gap-1.5 text-[11px] font-medium text-slate-500">
              {mode === 'hybrid' ? (
                <><Sparkles size={10} className="text-indigo-500" /> Hybrid · BM25 + semantic</>
              ) : (
                <>Keyword · exact substring</>
              )}
            </span>
            <span className="text-[11px] text-slate-400">
              {isFetching ? '…' : `${results.length} result${results.length === 1 ? '' : 's'}`}
            </span>
          </div>

          {results.length > 0 ? (
            <div className="max-h-72 overflow-y-auto">
              {results.map((node) => (
                <button
                  key={node.id}
                  onClick={() => pick(node)}
                  className="w-full flex items-center gap-2.5 px-3 py-2.5 hover:bg-slate-50 text-left transition-colors group"
                >
                  <NodeBadge label={node.label} />
                  <span className="text-sm text-slate-700 group-hover:text-slate-900 truncate transition-colors flex-1 min-w-0">
                    {node.name ?? node.id}
                  </span>
                  {mode === 'hybrid' && <MatchBadge match={node._match} />}
                </button>
              ))}
            </div>
          ) : (
            <div className="px-3 py-4 text-center">
              <p className="text-sm text-slate-400">
                {isFetching ? 'Searching…' : 'No matches'}
              </p>
              {noMatches && mode === 'keyword' && (
                <p className="mt-1 text-[11px] text-slate-400">
                  No exact substring match — try <button
                    onClick={() => setMode('hybrid')}
                    className="text-indigo-500 hover:text-indigo-600 font-medium"
                  >Hybrid</button> for semantic results.
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
