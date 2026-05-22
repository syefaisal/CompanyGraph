import { LABEL_BG } from '../lib/colors'
import type { NodeLabel } from '../types'

export function NodeBadge({ label }: { label: NodeLabel }) {
  return (
    <span className={`inline-flex items-center text-xs px-2 py-0.5 rounded-md border font-medium ${LABEL_BG[label]}`}>
      {label}
    </span>
  )
}
