import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Plus } from 'lucide-react'
import { api } from '../lib/api'
import { NODE_COLORS, NODE_LABELS } from '../lib/colors'
import type { NodeLabel } from '../types'

interface Props {
  onClose: () => void
}

export function AddNodeModal({ onClose }: Props) {
  const qc = useQueryClient()
  const [label, setLabel] = useState<NodeLabel>('Person')
  const [name, setName] = useState('')
  const [extra, setExtra] = useState('')
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: () => {
      let props: Record<string, unknown> = { name }
      if (extra.trim()) {
        try {
          props = { name, ...JSON.parse(extra) }
        } catch {
          throw new Error('Extra properties must be valid JSON')
        }
      }
      return api.createNode(label, props)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['graph'] })
      qc.invalidateQueries({ queryKey: ['health'] })
      onClose()
    },
    onError: (e: Error) => setError(e.message),
  })

  function submit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (!name.trim()) { setError('Name is required'); return }
    mutation.mutate()
  }

  const activeColor = NODE_COLORS[label]

  return (
    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      <div className="bg-white border border-slate-200 rounded-2xl shadow-modal w-full max-w-md">

        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center border"
              style={{ backgroundColor: `${activeColor}15`, borderColor: `${activeColor}40` }}
            >
              <Plus size={13} style={{ color: activeColor }} />
            </div>
            <h2 className="text-sm font-semibold text-slate-800">Add Node</h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 hover:bg-slate-100 p-1.5 rounded-lg transition-all"
          >
            <X size={14} />
          </button>
        </div>

        <form onSubmit={submit} className="p-5 space-y-4">
          <div>
            <label className="block text-xs text-slate-500 font-medium mb-2">Node type</label>
            <div className="flex gap-1.5 flex-wrap">
              {NODE_LABELS.map((l) => {
                const color = NODE_COLORS[l]
                const active = label === l
                return (
                  <button
                    key={l}
                    type="button"
                    onClick={() => setLabel(l)}
                    className="text-xs px-3 py-1.5 rounded-lg border font-medium transition-all duration-200"
                    style={{
                      borderColor:     active ? `${color}60` : '#e2e8f0',
                      color:           active ? color : '#94a3b8',
                      backgroundColor: active ? `${color}10` : 'transparent',
                    }}
                  >
                    {l}
                  </button>
                )
              })}
            </div>
          </div>

          <div>
            <label className="block text-xs text-slate-500 font-medium mb-2">
              Name <span className="text-slate-300 font-normal">(required)</span>
            </label>
            <input
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-800 placeholder-slate-400 outline-none focus:border-indigo-400 focus:bg-white transition-all"
              placeholder="e.g. Alice Johnson"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
          </div>

          <div>
            <label className="block text-xs text-slate-500 font-medium mb-2">
              Extra properties <span className="text-slate-300 font-normal">(JSON, optional)</span>
            </label>
            <textarea
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-800 placeholder-slate-400 outline-none focus:border-indigo-400 focus:bg-white transition-all font-mono resize-none"
              rows={3}
              placeholder='{"role": "Engineer", "team": "Platform"}'
              value={extra}
              onChange={(e) => setExtra(e.target.value)}
            />
          </div>

          {error && (
            <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-slate-500 hover:text-slate-700 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg transition-colors shadow-sm"
            >
              {mutation.isPending ? (
                <>
                  <div className="w-3.5 h-3.5 border border-white/30 border-t-white rounded-full animate-spin" />
                  Creating…
                </>
              ) : (
                <>
                  <Plus size={13} />
                  Create
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
