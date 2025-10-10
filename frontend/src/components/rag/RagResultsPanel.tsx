import { useMemo } from 'react'

type RagItem = {
  content?: string
  text?: string
  score?: number
  source?: string
  citation?: string
  metadata?: Record<string, any>
}

function highlightText(text: string, query?: string) {
  if (!query || !text) return text
  const terms = query
    .split(/\s+/)
    .map((t) => t.trim())
    .filter(Boolean)
  if (terms.length === 0) return text
  const pattern = new RegExp(`(${terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi')
  return text.split(pattern).map((chunk, idx) => {
    if (pattern.test(chunk)) {
      return (
        <mark key={idx} className="bg-yellow-200">
          {chunk}
        </mark>
      )
    }
    return <span key={idx}>{chunk}</span>
  })
}

export default function RagResultsPanel({ result, query }: { result: any; query?: string }) {
  const items: RagItem[] = useMemo(() => {
    if (!result) return []
    const candidates = [result?.results, result?.documents, result?.chunks, result?.items]
    const list = candidates.find((arr) => Array.isArray(arr)) || []
    return (list as any[]).map((it) => ({
      content: it.content ?? it.text ?? it.body ?? '',
      score: it.score ?? it.similarity ?? undefined,
      source: it.source ?? it.url ?? it.path ?? undefined,
      citation: it.citation ?? it.ref ?? undefined,
      metadata: it.metadata ?? {},
    }))
  }, [result])

  if (!items || items.length === 0) {
    return <div className="text-sm text-muted-foreground">无检索证据</div>
  }

  return (
    <div className="space-y-3">
      <div className="text-sm font-medium">检索证据（{items.length}）</div>
      <ul className="space-y-2">
        {items.map((it, idx) => (
          <li key={`rag-${idx}`} className="border rounded p-3">
            <div className="text-xs text-muted-foreground mb-2 flex gap-3">
              {typeof it.score !== 'undefined' ? <span>score: {Number(it.score).toFixed(3)}</span> : null}
              {it.source ? (
                <a
                  href={it.source}
                  target="_blank"
                  rel="noreferrer"
                  className="underline decoration-dotted"
                >
                  {it.source}
                </a>
              ) : null}
              {it.citation ? <span>citation: {it.citation}</span> : null}
            </div>
            <div className="text-sm leading-relaxed break-words">
              {highlightText(it.content || '', query)}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}