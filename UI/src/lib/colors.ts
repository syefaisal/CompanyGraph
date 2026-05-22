import type { NodeLabel } from '../types'

export const NODE_COLORS: Record<NodeLabel, string> = {
  Person:   '#3b82f6',   // blue-500
  Product:  '#8b5cf6',   // violet-500
  Customer: '#10b981',   // emerald-500
  Workflow: '#f59e0b',   // amber-500
  Decision: '#ef4444',   // red-500
}

export const NODE_DARK: Record<NodeLabel, string> = {
  Person:   '#1d4ed8',
  Product:  '#6d28d9',
  Customer: '#047857',
  Workflow: '#b45309',
  Decision: '#b91c1c',
}

export const NODE_GLOW: Record<NodeLabel, string> = {
  Person:   'rgba(59,130,246,0.35)',
  Product:  'rgba(139,92,246,0.35)',
  Customer: 'rgba(16,185,129,0.35)',
  Workflow: 'rgba(245,158,11,0.35)',
  Decision: 'rgba(239,68,68,0.35)',
}

// Light-theme badge styles
export const LABEL_BG: Record<NodeLabel, string> = {
  Person:   'bg-blue-50    text-blue-700    border-blue-200',
  Product:  'bg-violet-50  text-violet-700  border-violet-200',
  Customer: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  Workflow: 'bg-amber-50   text-amber-700   border-amber-200',
  Decision: 'bg-red-50     text-red-700     border-red-200',
}

export const NODE_LABELS: NodeLabel[] = [
  'Person',
  'Product',
  'Customer',
  'Workflow',
  'Decision',
]
