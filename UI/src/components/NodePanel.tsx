import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Trash2, Zap, ArrowRight, ArrowLeft, ChevronRight } from 'lucide-react'
import { api } from '../lib/api'
import { NODE_COLORS } from '../lib/colors'
import { NodeBadge } from './NodeBadge'
import type { GraphNode, NodeLabel } from '../types'

interface Props {
  nodeId: string
  onClose: () => void
  onNavigate: (id: string) => void
}

export function NodePanel({ nodeId, onClose, onNavigate }: Props) {
  const qc = useQueryClient()

  const { data: node, isLoading } = useQuery({
    queryKey: ['node', nodeId],
    queryFn: () => api.getNode(nodeId),
  })

  const { data: impact } = useQuery({
    queryKey: ['impact', nodeId],
    queryFn: () => api.impact(nodeId),
  })

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteNode(nodeId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['graph'] })
      qc.invalidateQueries({ queryKey: ['health'] })
      onClose()
    },
  })

  if (isLoading || !node) {
    return (
      <div className="h-full flex items-center justify-center bg-white">
        <div className="relative w-7 h-7">
          <div className="absolute inset-0 rounded-full border border-slate-200" />
          <div className="absolute inset-0 rounded-full border border-t-indigo-500 animate-spin" />
        </div>
      </div>
    )
  }

  const color = NODE_COLORS[node.label]
  const name = node.name ?? node.id
  const outgoing = node.connections.filter((c) => c.direction === 'out')
  const incoming = node.connections.filter((c) => c.direction === 'in')
  const extraProps = Object.entries(node).filter(
    ([k]) => !['name', 'id', 'label', '_labels', 'connections'].includes(k)
  )

  return (
    <div className="h-full flex flex-col overflow-hidden bg-white">

      {/* Header */}
      <div className="p-4 border-b border-slate-200 shrink-0 relative">
        <div
          className="absolute left-0 top-0 bottom-0 w-0.5"
          style={{ backgroundColor: color }}
        />
        <div className="flex items-start justify-between gap-2 pl-2">
          <div className="min-w-0">
            <div className="mb-1.5">
              <NodeBadge label={node.label} />
            </div>
            <h2 className="text-base font-semibold text-slate-900 leading-snug">{name}</h2>
            <p className="text-xs text-slate-400 mt-0.5 font-mono tracking-tight truncate">{node.id}</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 hover:bg-slate-100 p-1 rounded-lg transition-all shrink-0"
          >
            <X size={14} />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">

        {extraProps.length > 0 && (
          <section className="p-4 border-b border-slate-100">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2.5">Properties</h3>
            <div className="space-y-1.5">
              {extraProps.map(([k, v]) => (
                <div key={k} className="flex gap-2 px-3 py-1.5 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-xs text-slate-400 shrink-0 capitalize w-24 truncate">{k}</span>
                  <span className="text-xs text-slate-700 truncate font-medium">{String(v)}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {outgoing.length > 0 && (
          <section className="p-4 border-b border-slate-100">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2.5 flex items-center gap-1.5">
              <ArrowRight size={11} />
              Outgoing
              <span className="ml-auto font-normal normal-case tracking-normal text-slate-300">{outgoing.length}</span>
            </h3>
            <div className="space-y-0.5">
              {outgoing.map((c, i) => (
                <button
                  key={i}
                  onClick={() => onNavigate(c.neighbor_id)}
                  className="w-full flex items-center gap-2 text-left text-xs px-3 py-2 rounded-lg hover:bg-slate-50 transition-colors group"
                >
                  <span className="text-slate-400 font-mono shrink-0 text-[10px] uppercase tracking-wide">{c.rel_type}</span>
                  <ChevronRight size={10} className="text-slate-300 group-hover:text-slate-400 transition-colors" />
                  <span className="text-slate-600 group-hover:text-slate-900 truncate transition-colors flex-1">{c.neighbor_name}</span>
                  <NodeBadge label={(c.neighbor_labels[0] ?? 'Person') as NodeLabel} />
                </button>
              ))}
            </div>
          </section>
        )}

        {incoming.length > 0 && (
          <section className="p-4 border-b border-slate-100">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2.5 flex items-center gap-1.5">
              <ArrowLeft size={11} />
              Incoming
              <span className="ml-auto font-normal normal-case tracking-normal text-slate-300">{incoming.length}</span>
            </h3>
            <div className="space-y-0.5">
              {incoming.map((c, i) => (
                <button
                  key={i}
                  onClick={() => onNavigate(c.neighbor_id)}
                  className="w-full flex items-center gap-2 text-left text-xs px-3 py-2 rounded-lg hover:bg-slate-50 transition-colors group"
                >
                  <NodeBadge label={(c.neighbor_labels[0] ?? 'Person') as NodeLabel} />
                  <span className="text-slate-600 group-hover:text-slate-900 truncate transition-colors flex-1">{c.neighbor_name}</span>
                  <ChevronRight size={10} className="text-slate-300 rotate-180 group-hover:text-slate-400 transition-colors" />
                  <span className="text-slate-400 font-mono shrink-0 text-[10px] uppercase tracking-wide">{c.rel_type}</span>
                </button>
              ))}
            </div>
          </section>
        )}

        {impact && impact.reachable.length > 0 && (
          <section className="p-4 border-b border-slate-100">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2.5 flex items-center gap-1.5">
              <Zap size={11} className="text-amber-500" />
              Impact
              <span className="ml-auto font-normal normal-case tracking-normal text-slate-300">{impact.reachable.length} reachable</span>
            </h3>
            <div className="space-y-0.5">
              {impact.reachable.slice(0, 8).map((r, i) => (
                <button
                  key={i}
                  onClick={() => onNavigate(r.node.id)}
                  className="w-full flex items-center gap-2 text-left text-xs px-3 py-2 rounded-lg hover:bg-slate-50 transition-colors group"
                >
                  <span className="text-slate-300 font-mono shrink-0 w-5 text-right">{r.hops}h</span>
                  <NodeBadge label={r.node.label} />
                  <span className="text-slate-600 group-hover:text-slate-900 truncate transition-colors flex-1">{r.node.name}</span>
                </button>
              ))}
              {impact.reachable.length > 8 && (
                <p className="text-xs text-slate-400 pl-3 pt-1">+{impact.reachable.length - 8} more nodes reachable</p>
              )}
            </div>
          </section>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-slate-100 shrink-0">
        <button
          onClick={() => {
            if (confirm(`Delete "${name}"? This cannot be undone.`)) deleteMutation.mutate()
          }}
          disabled={deleteMutation.isPending}
          className="flex items-center gap-2 text-xs text-slate-400 hover:text-red-500 disabled:opacity-40 transition-colors group"
        >
          <Trash2 size={13} className="group-hover:text-red-500 transition-colors" />
          {deleteMutation.isPending ? 'Deleting…' : 'Delete node'}
        </button>
      </div>
    </div>
  )
}

export type { GraphNode }
