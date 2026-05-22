import { NODE_COLORS, NODE_LABELS } from '../lib/colors'
import type { NodeLabel } from '../types'

interface Props {
  hidden: Set<NodeLabel>
  onToggle: (label: NodeLabel) => void
}

export function FilterChips({ hidden, onToggle }: Props) {
  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      <span className="text-xs text-slate-400 font-medium mr-0.5 select-none">Show</span>
      {NODE_LABELS.map((label) => {
        const active = !hidden.has(label)
        const color = NODE_COLORS[label]
        return (
          <button
            key={label}
            onClick={() => onToggle(label)}
            title={active ? `Hide ${label}` : `Show ${label}`}
            className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border transition-all duration-200 select-none font-medium"
            style={{
              borderColor:     active ? `${color}70` : '#e2e8f0',
              color:           active ? color : '#94a3b8',
              backgroundColor: active ? `${color}12` : 'transparent',
            }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full shrink-0 transition-all duration-200"
              style={{
                backgroundColor: active ? color : '#cbd5e1',
                boxShadow: active ? `0 0 5px ${color}` : 'none',
              }}
            />
            {label}
          </button>
        )
      })}
    </div>
  )
}
