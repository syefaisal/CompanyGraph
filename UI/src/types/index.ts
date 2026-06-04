export type NodeLabel = 'Person' | 'Product' | 'Customer' | 'Workflow' | 'Decision'

export interface MatchInfo {
  lexical: boolean
  semantic: boolean
  bm25_score: number | null
  semantic_score: number | null
}

export interface GraphNode {
  id: string
  label: NodeLabel
  _labels: string[]
  name: string
  _match?: MatchInfo
  [key: string]: unknown
}

export interface GraphRelationship {
  type: string
  from_id: string
  to_id: string
  [key: string]: unknown
}

export interface FullGraph {
  nodes: GraphNode[]
  relationships: GraphRelationship[]
}

export interface NodeConnection {
  rel_type: string
  direction: 'in' | 'out'
  neighbor_id: string
  neighbor_name: string
  neighbor_labels: string[]
}

export interface NodeWithConnections extends GraphNode {
  connections: NodeConnection[]
}

export interface GraphStats {
  nodes: Record<string, number>
  relationships: number
}

export interface ImpactResult {
  source: GraphNode
  reachable: Array<{ node: GraphNode; hops: number }>
}

// react-force-graph node shape
export interface FGNode {
  id: string
  label: NodeLabel
  name: string
  // positions added by force-graph at runtime
  x?: number
  y?: number
  vx?: number
  vy?: number
  fx?: number
  fy?: number
}

export interface FGLink {
  source: string
  target: string
  type: string
}
