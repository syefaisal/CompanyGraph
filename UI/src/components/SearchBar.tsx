import { useState, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, X } from 'lucide-react'
import { api } from '../lib/api'
import { NodeBadge } from './NodeBadge'
import type { GraphNode } from '../types'

interface Props {
  onSelect: (node: GraphNode) => void
}

export function SearchBar({ onSelect }: Props) {
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const { data: results = [] } = useQuery({
    queryKey: ['search', q],
    queryFn: () => api.search(q),
    enabled: q.trim().length >= 2,
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

  return (
    <div ref={ref} className="relative w-64">
      <div className={`flex items-center gap-2 bg-white border rounded-lg px-3 py-2 transition-all duration-200 ${
        open && results.length > 0 ? 'border-indigo-400 shadow-sm' : 'border-slate-200 hover:border-slate-300'
      }`}>
        <Search size={13} className="text-slate-400 shrink-0" />
        <input
          className="bg-transparent text-sm text-slate-800 placeholder-slate-400 outline-none flex-1 min-w-0"
          placeholder="Search nodes…"
          value={q}
          onChange={(e) => { setQ(e.target.value); setOpen(true) }}
          onFocus={() => setOpen(true)}
        />
        {q && (
          <button
            onClick={() => { setQ(''); setOpen(false) }}
            className="text-slate-300 hover:text-slate-500 transition-colors"
          >
            <X size={12} />
          </button>
        )}
      </div>

      {open && results.length > 0 && (
        <div className="absolute top-full mt-1.5 left-0 right-0 bg-white border border-slate-200 rounded-xl shadow-panel z-50 overflow-hidden max-h-72 overflow-y-auto animate-fade-in">
          {results.map((node) => (
            <button
              key={node.id}
              onClick={() => pick(node)}
              className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-slate-50 text-left transition-colors group"
            >
              <NodeBadge label={node.label} />
              <span className="text-sm text-slate-700 group-hover:text-slate-900 truncate transition-colors">
                {node.name ?? node.id}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
