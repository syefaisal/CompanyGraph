import { useState, useRef, useEffect, useCallback } from 'react'
import {
  Send, Zap, Loader2, User, RotateCcw, ChevronRight,
  ThumbsUp, ThumbsDown, CheckCircle, Flag, MessageSquare, X,
} from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
  error?: boolean
  feedback?: 'approved' | 'flagged'
  reviewComment?: string
}

const SUGGESTIONS = [
  { icon: '👥', text: 'Who owns the Lease Renewal workflow and who else is involved?' },
  { icon: '⚖️', text: 'Trace the full impact of the GDPR and CCPA compliance overhaul.' },
  { icon: '🔗', text: 'Find the connection between Elena Rodriguez and Apex Commercial.' },
  { icon: '🏢', text: 'Which products does Sunstone Residential use and who built them?' },
  { icon: '⚠️', text: 'What workflows would be at risk if Marcus Webb left the company?' },
  { icon: '➕', text: "Add a new compliance engineer named 'Kai Patel' and connect them to the Fair Housing Audit workflow." },
]

function renderMarkdown(text: string) {
  return text.split('\n').map((line, i) => {
    if (line.startsWith('### ')) return <h3 key={i} className="text-sm font-semibold text-slate-900 mt-3 mb-1">{fmt(line.slice(4))}</h3>
    if (line.startsWith('## '))  return <h2 key={i} className="text-sm font-bold text-slate-900 mt-4 mb-1.5">{fmt(line.slice(3))}</h2>
    if (line.startsWith('# '))   return <h1 key={i} className="text-base font-bold text-slate-900 mt-4 mb-2">{fmt(line.slice(2))}</h1>
    if (line.startsWith('- ') || line.startsWith('* ')) {
      return (
        <div key={i} className="flex gap-2 text-sm leading-relaxed">
          <span className="text-indigo-500 mt-0.5 shrink-0">•</span>
          <span className="text-slate-700">{fmt(line.slice(2))}</span>
        </div>
      )
    }
    if (/^\d+\. /.test(line)) {
      const num = line.match(/^(\d+)/)?.[1]
      return (
        <div key={i} className="flex gap-2 text-sm leading-relaxed">
          <span className="text-indigo-500 shrink-0 w-5 text-right font-medium">{num}.</span>
          <span className="text-slate-700">{fmt(line.replace(/^\d+\. /, ''))}</span>
        </div>
      )
    }
    if (line.startsWith('---')) return <hr key={i} className="border-slate-200 my-2" />
    if (line.trim() === '') return <div key={i} className="h-1.5" />
    return <p key={i} className="text-sm leading-relaxed text-slate-700">{fmt(line)}</p>
  })
}

function fmt(text: string): React.ReactNode {
  return text.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g).map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**'))
      return <strong key={i} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>
    if (part.startsWith('`') && part.endsWith('`'))
      return <code key={i} className="font-mono text-xs bg-indigo-50 border border-indigo-100 text-indigo-700 rounded px-1.5 py-0.5">{part.slice(1, -1)}</code>
    if (part.startsWith('*') && part.endsWith('*'))
      return <em key={i} className="italic">{part.slice(1, -1)}</em>
    return part
  })
}

// Truncate long text for the review panel
function truncate(text: string, n = 80) {
  return text.length > n ? text.slice(0, n).trimEnd() + '…' : text
}

export function QueryPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [lastAsked, setLastAsked] = useState<string | null>(null)
  // Index of the message currently showing the flag comment form
  const [flaggingIdx, setFlaggingIdx] = useState<number | null>(null)
  const [commentDraft, setCommentDraft] = useState('')
  // Sidebar tab: 'queries' | 'review'
  const [sideTab, setSideTab] = useState<'queries' | 'review'>('queries')

  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const flaggedMessages = messages
    .map((m, i) => ({ ...m, idx: i }))
    .filter((m) => m.role === 'assistant' && m.feedback === 'flagged')

  // Auto-switch to review tab when first flag is submitted
  const prevFlagCount = useRef(0)
  useEffect(() => {
    if (flaggedMessages.length > prevFlagCount.current) {
      setSideTab('review')
    }
    prevFlagCount.current = flaggedMessages.length
  }, [flaggedMessages.length])

  function approve(idx: number) {
    setMessages((prev) =>
      prev.map((m, i) => i === idx ? { ...m, feedback: 'approved', reviewComment: undefined } : m)
    )
    if (flaggingIdx === idx) setFlaggingIdx(null)
  }

  function openFlag(idx: number) {
    setFlaggingIdx(idx)
    setCommentDraft('')
  }

  function submitFlag(idx: number) {
    setMessages((prev) =>
      prev.map((m, i) => i === idx ? { ...m, feedback: 'flagged', reviewComment: commentDraft.trim() || undefined } : m)
    )
    setFlaggingIdx(null)
    setCommentDraft('')
  }

  function clearFeedback(idx: number) {
    setMessages((prev) =>
      prev.map((m, i) => i === idx ? { ...m, feedback: undefined, reviewComment: undefined } : m)
    )
  }

  const ask = useCallback(async (question: string) => {
    if (!question.trim() || loading) return
    setLastAsked(question)
    setFlaggingIdx(null)
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: question },
      { role: 'assistant', content: '', streaming: true },
    ])
    setInput('')
    setLoading(true)
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error((err as { detail?: string }).detail ?? `${res.status}`)
      }
      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const event = JSON.parse(line.slice(6))
            if (event.type === 'text') {
              setMessages((prev) => {
                const next = [...prev]
                const last = next[next.length - 1]
                if (last?.role === 'assistant') next[next.length - 1] = { ...last, content: last.content + event.content }
                return next
              })
            } else if (event.type === 'done') {
              setMessages((prev) => {
                const next = [...prev]
                const last = next[next.length - 1]
                if (last?.role === 'assistant') next[next.length - 1] = { ...last, streaming: false }
                return next
              })
            } else if (event.type === 'error') {
              throw new Error(event.content)
            }
          } catch { /* ignore malformed SSE */ }
        }
      }
    } catch (err) {
      setMessages((prev) => {
        const next = [...prev]
        const last = next[next.length - 1]
        if (last?.role === 'assistant') {
          next[next.length - 1] = {
            ...last,
            content: err instanceof Error ? err.message : 'Request failed',
            streaming: false,
            error: true,
          }
        }
        return next
      })
    } finally {
      setLoading(false)
    }
  }, [loading])

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      ask(input)
    }
  }

  return (
    <div className="flex h-full bg-slate-50 overflow-hidden">

      {/* ── Sidebar ──────────────────────────────────────────────────── */}
      <aside className="w-64 shrink-0 bg-white border-r border-slate-200 flex flex-col overflow-hidden">

        {/* Sidebar tabs */}
        <div className="flex border-b border-slate-200 shrink-0">
          <button
            onClick={() => setSideTab('queries')}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium transition-colors ${
              sideTab === 'queries'
                ? 'text-indigo-600 border-b-2 border-indigo-500 bg-indigo-50/50'
                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
            }`}
          >
            <Zap size={11} />
            Samples
          </button>
          <button
            onClick={() => setSideTab('review')}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium transition-colors ${
              sideTab === 'review'
                ? 'text-amber-600 border-b-2 border-amber-500 bg-amber-50/50'
                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
            }`}
          >
            <Flag size={11} />
            Review
            {flaggedMessages.length > 0 && (
              <span className="ml-1 bg-amber-500 text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
                {flaggedMessages.length}
              </span>
            )}
          </button>
        </div>

        {/* ── Samples tab ── */}
        {sideTab === 'queries' && (
          <>
            <div className="px-4 py-2.5 border-b border-slate-100">
              <p className="text-xs text-slate-400">Click any to send</p>
            </div>
            <div className="flex-1 overflow-y-auto py-2">
              {SUGGESTIONS.map((s) => {
                const isActive = lastAsked === s.text
                return (
                  <button
                    key={s.text}
                    onClick={() => ask(s.text)}
                    disabled={loading}
                    className={`w-full flex items-start gap-2.5 text-left px-3 py-2.5 transition-all duration-150 group border-r-2
                      ${isActive ? 'bg-indigo-50 border-indigo-500' : 'border-transparent hover:bg-slate-50'}
                      ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                    `}
                  >
                    <span className="text-base leading-none mt-0.5 shrink-0">{s.icon}</span>
                    <span className={`text-xs leading-snug transition-colors ${
                      isActive ? 'text-indigo-700 font-medium' : 'text-slate-600 group-hover:text-slate-900'
                    }`}>
                      {s.text}
                    </span>
                    <ChevronRight size={11} className={`shrink-0 mt-0.5 ml-auto transition-opacity ${
                      isActive ? 'text-indigo-400 opacity-100' : 'text-slate-300 opacity-0 group-hover:opacity-100'
                    }`} />
                  </button>
                )
              })}
            </div>
          </>
        )}

        {/* ── Review tab ── */}
        {sideTab === 'review' && (
          <div className="flex-1 overflow-y-auto">
            {flaggedMessages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full px-4 text-center py-12">
                <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center mb-3">
                  <Flag size={16} className="text-slate-400" />
                </div>
                <p className="text-xs font-medium text-slate-500 mb-1">No flagged responses</p>
                <p className="text-xs text-slate-400 leading-snug">
                  Use the thumbs down button on any answer to flag it for review.
                </p>
              </div>
            ) : (
              <div className="py-2 space-y-0.5">
                {flaggedMessages.map((m) => (
                  <div key={m.idx} className="px-3 py-2.5 border-b border-slate-100">
                    <div className="flex items-start gap-2 mb-1.5">
                      <Flag size={11} className="text-amber-500 shrink-0 mt-0.5" />
                      <p className="text-xs text-slate-700 leading-snug">{truncate(m.content)}</p>
                    </div>
                    {m.reviewComment && (
                      <div className="flex items-start gap-1.5 mt-1.5 pl-4">
                        <MessageSquare size={10} className="text-slate-400 shrink-0 mt-0.5" />
                        <p className="text-xs text-slate-500 italic leading-snug">"{m.reviewComment}"</p>
                      </div>
                    )}
                    <button
                      onClick={() => clearFeedback(m.idx)}
                      className="mt-1.5 ml-4 text-[10px] text-slate-400 hover:text-slate-600 transition-colors"
                    >
                      Clear flag
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* New conversation */}
        {messages.length > 0 && (
          <div className="p-3 border-t border-slate-100 shrink-0">
            <button
              onClick={() => { setMessages([]); setLastAsked(null); setFlaggingIdx(null) }}
              className="w-full flex items-center justify-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 py-2 rounded-lg hover:bg-slate-50 border border-slate-200 hover:border-slate-300 transition-all"
            >
              <RotateCcw size={11} />
              New conversation
            </button>
          </div>
        )}
      </aside>

      {/* ── Chat area ────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-8">
          <div className="max-w-2xl mx-auto">

            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full min-h-64 animate-fade-in text-center">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-indigo-50 border border-indigo-200 mb-4">
                  <Zap size={24} className="text-indigo-500" />
                </div>
                <h2 className="text-lg font-semibold text-slate-800 mb-1.5">Ask anything about Meridian Property Group</h2>
                <p className="text-sm text-slate-400 max-w-xs leading-relaxed">
                  Select a sample query from the left, or type your own question below.
                </p>
              </div>
            ) : (
              <div className="space-y-5">
                {messages.map((msg, i) => (
                  <div key={i} className={`flex gap-3 animate-fade-in ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>

                    <div className={`shrink-0 w-7 h-7 rounded-lg flex items-center justify-center mt-0.5 border ${
                      msg.role === 'user'
                        ? 'bg-indigo-600 border-indigo-700'
                        : msg.error
                          ? 'bg-red-50 border-red-200'
                          : 'bg-white border-slate-200 shadow-card'
                    }`}>
                      {msg.role === 'user'
                        ? <User size={12} className="text-white" />
                        : msg.error
                          ? <span className="text-red-500 text-xs font-bold">!</span>
                          : <Zap size={12} className="text-indigo-500" />}
                    </div>

                    <div className={`max-w-[88%] rounded-2xl px-4 py-3 ${
                      msg.role === 'user'
                        ? 'bg-indigo-600 text-white shadow-sm'
                        : msg.error
                          ? 'bg-red-50 border border-red-200 text-red-700'
                          : msg.feedback === 'flagged'
                            ? 'bg-white border border-amber-300 text-slate-700 shadow-card'
                            : msg.feedback === 'approved'
                              ? 'bg-white border border-emerald-300 text-slate-700 shadow-card'
                              : 'bg-white border border-slate-200 text-slate-700 shadow-card'
                    }`}>

                      {/* Message content */}
                      {msg.role === 'user' ? (
                        <p className="text-sm leading-relaxed">{msg.content}</p>
                      ) : (
                        <div className="space-y-0.5">
                          {msg.content
                            ? renderMarkdown(msg.content)
                            : msg.streaming
                              ? <span className="text-slate-400 text-sm">Thinking…</span>
                              : null}
                          {msg.streaming && (
                            <span className="inline-block w-0.5 h-4 bg-indigo-500 ml-0.5 align-text-bottom animate-blink" />
                          )}
                        </div>
                      )}

                      {/* Human review controls — assistant only, after streaming */}
                      {msg.role === 'assistant' && !msg.streaming && !msg.error && (
                        <div className="mt-3 pt-2.5 border-t border-slate-100">

                          {/* No feedback yet */}
                          {!msg.feedback && flaggingIdx !== i && (
                            <div className="flex items-center gap-1.5">
                              <span className="text-xs text-slate-400 mr-1">Was this helpful?</span>
                              <button
                                onClick={() => approve(i)}
                                className="flex items-center gap-1 text-xs text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 px-2 py-1 rounded-lg transition-all"
                              >
                                <ThumbsUp size={12} />
                                Yes
                              </button>
                              <button
                                onClick={() => openFlag(i)}
                                className="flex items-center gap-1 text-xs text-slate-400 hover:text-amber-600 hover:bg-amber-50 px-2 py-1 rounded-lg transition-all"
                              >
                                <ThumbsDown size={12} />
                                Flag
                              </button>
                            </div>
                          )}

                          {/* Flag comment form */}
                          {flaggingIdx === i && (
                            <div className="space-y-2 animate-fade-in">
                              <p className="text-xs font-medium text-amber-700">What's wrong with this response?</p>
                              <textarea
                                autoFocus
                                rows={2}
                                className="w-full text-xs text-slate-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 outline-none focus:border-amber-400 resize-none placeholder-amber-300"
                                placeholder="e.g. Incorrect relationship, missing nodes, wrong count…"
                                value={commentDraft}
                                onChange={(e) => setCommentDraft(e.target.value)}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitFlag(i) }
                                }}
                              />
                              <div className="flex items-center gap-2">
                                <button
                                  onClick={() => submitFlag(i)}
                                  className="flex items-center gap-1 text-xs bg-amber-500 hover:bg-amber-600 text-white px-2.5 py-1.5 rounded-lg transition-colors font-medium"
                                >
                                  <Flag size={11} />
                                  Submit flag
                                </button>
                                <button
                                  onClick={() => setFlaggingIdx(null)}
                                  className="text-xs text-slate-400 hover:text-slate-600 px-2 py-1.5 transition-colors"
                                >
                                  Cancel
                                </button>
                              </div>
                            </div>
                          )}

                          {/* Approved badge */}
                          {msg.feedback === 'approved' && (
                            <div className="flex items-center gap-2">
                              <div className="flex items-center gap-1.5 text-xs text-emerald-600 font-medium">
                                <CheckCircle size={12} />
                                Approved
                              </div>
                              <button
                                onClick={() => clearFeedback(i)}
                                className="text-slate-300 hover:text-slate-500 transition-colors"
                                title="Clear feedback"
                              >
                                <X size={11} />
                              </button>
                            </div>
                          )}

                          {/* Flagged badge */}
                          {msg.feedback === 'flagged' && (
                            <div className="flex items-center gap-2 flex-wrap">
                              <div className="flex items-center gap-1.5 text-xs text-amber-600 font-medium">
                                <Flag size={12} />
                                Flagged for review
                              </div>
                              {msg.reviewComment && (
                                <span className="text-xs text-slate-400 italic">"{msg.reviewComment}"</span>
                              )}
                              <button
                                onClick={() => clearFeedback(i)}
                                className="text-slate-300 hover:text-slate-500 transition-colors ml-auto"
                                title="Clear flag"
                              >
                                <X size={11} />
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={bottomRef} />
              </div>
            )}
          </div>
        </div>

        {/* Input bar */}
        <div className="shrink-0 border-t border-slate-200 bg-white px-5 py-4 shadow-[0_-1px_3px_0_rgb(0,0,0,0.04)]">
          <div className="max-w-2xl mx-auto flex gap-2.5 items-end">
            <div className="flex-1 bg-slate-50 border border-slate-200 rounded-xl overflow-hidden focus-within:border-indigo-400 focus-within:bg-white focus-within:shadow-sm transition-all">
              <textarea
                ref={textareaRef}
                rows={1}
                className="w-full resize-none bg-transparent px-4 py-3 text-sm text-slate-800 placeholder-slate-400 outline-none"
                placeholder="Ask a cross-functional question… (Enter to send)"
                value={input}
                onChange={(e) => {
                  setInput(e.target.value)
                  e.target.style.height = 'auto'
                  e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`
                }}
                onKeyDown={onKeyDown}
              />
            </div>
            <button
              onClick={() => ask(input)}
              disabled={!input.trim() || loading}
              className="shrink-0 w-10 h-10 flex items-center justify-center rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-35 disabled:cursor-not-allowed transition-all shadow-sm"
            >
              {loading
                ? <Loader2 size={15} className="text-white animate-spin" />
                : <Send size={14} className="text-white" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
