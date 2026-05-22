import { useRef, useCallback, useEffect } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { NODE_COLORS, NODE_GLOW } from '../lib/colors'
import type { FGLink, FGNode, NodeLabel } from '../types'

interface Props {
  nodes: FGNode[]
  links: FGLink[]
  selectedId: string | null
  focusId: string | null      // pans to this node; set only by search, never by click
  hiddenLabels: Set<NodeLabel>
  onNodeClick: (node: FGNode) => void
  onBackgroundClick: () => void
}

export function GraphCanvas({ nodes, links, selectedId, focusId, hiddenLabels, onNodeClick, onBackgroundClick }: Props) {
  const fgRef = useRef<{
    zoom: (n: number, ms: number) => void
    centerAt: (x: number, y: number, ms: number) => void
  } | null>(null)

  const visibleNodes = nodes.filter((n) => !hiddenLabels.has(n.label))
  const visibleIds = new Set(visibleNodes.map((n) => n.id))
  const visibleLinks = links.filter((l) => visibleIds.has(l.source) && visibleIds.has(l.target))

  useEffect(() => {
    if (!focusId || !fgRef.current) return
    const node = visibleNodes.find((n) => n.id === focusId)
    if (node?.x !== undefined && node?.y !== undefined) {
      fgRef.current.centerAt(node.x, node.y, 600)
    }
  }, [focusId]) // eslint-disable-line react-hooks/exhaustive-deps

  const paintNode = useCallback(
    (node: FGNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const x = node.x ?? 0
      const y = node.y ?? 0
      const color = NODE_COLORS[node.label]
      const glowColor = NODE_GLOW[node.label]
      const isSelected = node.id === selectedId
      const radius = isSelected ? 11 : 7.5

      // Soft glow
      ctx.shadowBlur = isSelected ? 20 : 10
      ctx.shadowColor = isSelected ? color : glowColor

      // Filled circle — radial gradient for depth
      const grad = ctx.createRadialGradient(x - radius * 0.3, y - radius * 0.35, 0, x, y, radius)
      grad.addColorStop(0, isSelected ? '#ffffff' : lighten(color, 0.45))
      grad.addColorStop(1, color)
      ctx.beginPath()
      ctx.arc(x, y, radius, 0, 2 * Math.PI)
      ctx.fillStyle = grad
      ctx.fill()

      // Ring
      ctx.shadowBlur = 0
      ctx.strokeStyle = isSelected ? color : `${color}80`
      ctx.lineWidth = isSelected ? 2.5 : 1.5
      ctx.stroke()

      // Specular highlight
      ctx.beginPath()
      ctx.arc(x - radius * 0.25, y - radius * 0.3, radius * 0.2, 0, 2 * Math.PI)
      ctx.fillStyle = isSelected ? 'rgba(255,255,255,0.6)' : 'rgba(255,255,255,0.4)'
      ctx.fill()

      // Label
      if (globalScale > 0.7 || isSelected) {
        const rawSize = isSelected ? 12 / globalScale : 10 / globalScale
        const fontSize = Math.max(rawSize, isSelected ? 4.5 : 3.5)
        ctx.font = `${isSelected ? '600' : '500'} ${fontSize}px Inter, sans-serif`
        ctx.textAlign = 'center'
        ctx.textBaseline = 'top'
        const label = node.name ?? node.id
        const textY = y + radius + 3

        // Halo so text is readable on the light grid
        ctx.fillStyle = 'rgba(241,245,249,0.85)'
        for (const [dx, dy] of [[-0.5,0],[0.5,0],[0,-0.5],[0,0.5]]) {
          ctx.fillText(label, x + dx, textY + dy)
        }

        ctx.fillStyle = isSelected ? '#1e293b' : '#374151'
        ctx.fillText(label, x, textY)
        ctx.textBaseline = 'alphabetic'
      }
    },
    [selectedId]
  )

  return (
    <div className="w-full h-full graph-grid">
      <ForceGraph2D
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ref={fgRef as any}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        graphData={{ nodes: visibleNodes as any[], links: visibleLinks as any[] }}
        nodeId="id"
        nodeLabel={(n) => `${(n as FGNode).label}: ${(n as FGNode).name}`}
        nodeCanvasObject={(n, ctx, gs) => paintNode(n as FGNode, ctx, gs)}
        nodeCanvasObjectMode={() => 'replace'}
        linkColor={() => '#94a3b8'}
        linkWidth={1.5}
        linkDirectionalArrowLength={5}
        linkDirectionalArrowRelPos={1}
        linkDirectionalArrowColor={() => '#64748b'}
        linkDirectionalParticles={2}
        linkDirectionalParticleSpeed={0.005}
        linkDirectionalParticleWidth={2}
        linkDirectionalParticleColor={() => '#6366f1'}
        linkLabel={(l) => (l as FGLink).type}
        backgroundColor="transparent"
        onNodeClick={(n) => onNodeClick(n as FGNode)}
        onBackgroundClick={onBackgroundClick}
        cooldownTicks={150}
        d3AlphaDecay={0.015}
        d3VelocityDecay={0.25}
      />
    </div>
  )
}

function lighten(hex: string, amount: number): string {
  const num = parseInt(hex.slice(1), 16)
  const r = Math.min(255, (num >> 16) + Math.round(255 * amount))
  const g = Math.min(255, ((num >> 8) & 0xff) + Math.round(255 * amount))
  const b = Math.min(255, (num & 0xff) + Math.round(255 * amount))
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`
}
