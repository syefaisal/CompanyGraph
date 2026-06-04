import { Sparkles, Type } from 'lucide-react'
import type { MatchInfo } from '../types'

/**
 * Shows which retrieval arm(s) matched a hybrid-search result:
 *   • lexical  → BM25 token match
 *   • semantic → embedding cosine match (with score)
 * A result can be matched by one or both arms.
 */
export function MatchBadge({ match }: { match?: MatchInfo }) {
  if (!match) return null

  return (
    <span className="inline-flex items-center gap-1 shrink-0">
      {match.lexical && (
        <span
          title={`BM25 lexical match (score ${match.bm25_score ?? '—'})`}
          className="inline-flex items-center gap-0.5 text-[10px] font-medium px-1.5 py-0.5 rounded border border-amber-200 bg-amber-50 text-amber-700"
        >
          <Type size={9} />
          lexical
        </span>
      )}
      {match.semantic && (
        <span
          title={`Semantic embedding match (cosine ${match.semantic_score ?? '—'})`}
          className="inline-flex items-center gap-0.5 text-[10px] font-medium px-1.5 py-0.5 rounded border border-indigo-200 bg-indigo-50 text-indigo-700"
        >
          <Sparkles size={9} />
          semantic
          {match.semantic_score != null && (
            <span className="tabular-nums opacity-70">{match.semantic_score.toFixed(2)}</span>
          )}
        </span>
      )}
    </span>
  )
}
