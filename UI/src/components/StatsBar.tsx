import { useQuery } from '@tanstack/react-query'
import { Users, Box, ShoppingBag, Workflow, Lightbulb, Share2 } from 'lucide-react'
import { api } from '../lib/api'
import { NODE_COLORS } from '../lib/colors'

const ICONS: Record<string, React.ElementType> = {
  Person: Users,
  Product: Box,
  Customer: ShoppingBag,
  Workflow,
  Decision: Lightbulb,
}

export function StatsBar() {
  const { data } = useQuery({
    queryKey: ['health'],
    queryFn: api.health,
    refetchInterval: 30_000,
  })

  const stats = data?.stats
  const nodeCount = stats ? Object.values(stats.nodes).reduce((a, b) => a + b, 0) : null

  return (
    <div className="flex items-center gap-1.5">
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 text-xs">
        <span className="text-emerald-600 font-semibold tabular-nums">{nodeCount ?? '–'}</span>
        <span className="text-slate-500">nodes</span>
      </div>
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 text-xs">
        <Share2 size={10} className="text-sky-500" />
        <span className="text-sky-600 font-semibold tabular-nums">{stats?.relationships ?? '–'}</span>
        <span className="text-slate-500">edges</span>
      </div>
      {stats && Object.entries(stats.nodes).map(([label, count]) => {
        const Icon = ICONS[label]
        const color = NODE_COLORS[label as keyof typeof NODE_COLORS]
        return (
          <div
            key={label}
            className="hidden lg:flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium"
            style={{ color }}
            title={`${count} ${label}s`}
          >
            {Icon && <Icon size={11} />}
            <span className="tabular-nums">{count}</span>
          </div>
        )
      })}
    </div>
  )
}
