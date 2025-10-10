import { useMemo } from 'react'
import { Link } from 'react-router-dom'

type GraphLike = {
  nodes?: any[]
  edges?: any[]
  relationships?: any[]
  graph?: { nodes?: any[]; edges?: any[] }
}

export default function GraphStatsPanel({ result }: { result: GraphLike }) {
  const stats = useMemo(() => {
    const nodes = result?.nodes ?? result?.graph?.nodes ?? []
    const edges = result?.edges ?? result?.relationships ?? result?.graph?.edges ?? []
    const nodeCount = Array.isArray(nodes) ? nodes.length : 0
    const edgeCount = Array.isArray(edges) ? edges.length : 0
    const byType: Record<string, number> = {}
    if (Array.isArray(edges)) {
      edges.forEach((e: any) => {
        const t = e.type ?? e.label ?? 'UNKNOWN'
        byType[t] = (byType[t] || 0) + 1
      })
    }
    return { nodeCount, edgeCount, byType }
  }, [result])

  return (
    <div className="space-y-3">
      <div className="text-sm font-medium">图谱统计</div>
      <div className="grid grid-cols-2 gap-3">
        <div className="border rounded p-3">
          <div className="text-xs text-muted-foreground">节点数</div>
          <div className="text-xl font-semibold">{stats.nodeCount}</div>
        </div>
        <div className="border rounded p-3">
          <div className="text-xs text-muted-foreground">关系数</div>
          <div className="text-xl font-semibold">{stats.edgeCount}</div>
        </div>
      </div>
      <div>
        <div className="text-xs text-muted-foreground mb-1">关系分布</div>
        <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {Object.entries(stats.byType).map(([type, count]) => (
            <li key={type} className="border rounded p-2 text-sm flex justify-between">
              <span>{type}</span>
              <span className="text-muted-foreground">{count}</span>
            </li>
          ))}
          {Object.keys(stats.byType).length === 0 ? (
            <li className="text-sm text-muted-foreground">无关系类型</li>
          ) : null}
        </ul>
      </div>
      <div>
        <Link to="/graph" className="underline decoration-dotted text-sm">
          打开图谱工作台
        </Link>
      </div>
    </div>
  )
}