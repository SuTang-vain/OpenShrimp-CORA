import React, { useMemo, useState, useRef, useEffect } from 'react'
import GraphStatsPanel from '@/components/graph/GraphStatsPanel'

type NodeLike = { id?: string | number; label?: string; [k: string]: any }
type EdgeLike = { source?: any; target?: any; from?: any; to?: any; type?: string; [k: string]: any }

function getEdgeEnds(e: EdgeLike) {
  const s = e.source ?? e.from
  const t = e.target ?? e.to
  return { s, t }
}

type LayoutResult = {
  width: number
  height: number
  positions: Array<{ x: number; y: number; id?: any }>
  lines: Array<{ x1: number; y1: number; x2: number; y2: number; type?: string; sId?: any; tId?: any }>
}

function computeCircularLayout(nodes: NodeLike[], edges: EdgeLike[], width = 800, height = 480): LayoutResult {
  const cx = width / 2
  const cy = height / 2
  const radius = Math.max(120, Math.min(width, height) / 2 - 40)

  const ids = nodes.map((n, i) => (n.id ?? i))
  const idToIndex = new Map(ids.map((id, i) => [id, i]))

  const positions = nodes.map((_, i) => {
    const angle = (2 * Math.PI * i) / Math.max(1, nodes.length)
    const x = cx + radius * Math.cos(angle)
    const y = cy + radius * Math.sin(angle)
    return { x, y }
  })

  const lines = edges
    .map((e) => {
      const { s, t } = getEdgeEnds(e)
      const si = idToIndex.get(s)
      const ti = idToIndex.get(t)
      if (si == null || ti == null) return null
      return { x1: positions[si].x, y1: positions[si].y, x2: positions[ti].x, y2: positions[ti].y, type: e.type, sId: s, tId: t }
    })
    .filter(Boolean) as LayoutResult['lines']

  return { width, height, positions, lines }
}

function computeHierarchicalLayout(nodes: NodeLike[], edges: EdgeLike[], width = 900, height = 520): LayoutResult {
  const ids = nodes.map((n, i) => (n.id ?? i))
  const idToIndex = new Map(ids.map((id, i) => [id, i]))
  const indeg = new Map<any, number>(ids.map((id) => [id, 0]))
  const adj = new Map<any, any[]>()
  for (const id of ids) adj.set(id, [])
  for (const e of edges) {
    const { s, t } = getEdgeEnds(e)
    if (adj.has(s)) adj.get(s)!.push(t)
    if (indeg.has(t)) indeg.set(t, (indeg.get(t) || 0) + 1)
  }
  const sources = ids.filter((id) => (indeg.get(id) || 0) === 0)
  const layer = new Map<any, number>()
  const queue: any[] = [...sources]
  sources.forEach((id) => layer.set(id, 0))
  while (queue.length) {
    const u = queue.shift()
    const base = layer.get(u) || 0
    for (const v of adj.get(u) || []) {
      const lv = Math.max(base + 1, layer.get(v) || 0)
      if (lv !== (layer.get(v) || 0)) {
        layer.set(v, lv)
        queue.push(v)
      }
    }
  }
  // 未覆盖的节点设为0层
  for (const id of ids) if (!layer.has(id)) layer.set(id, 0)
  const grouped: Record<number, any[]> = {}
  for (const id of ids) {
    const lv = layer.get(id) || 0
    if (!grouped[lv]) grouped[lv] = []
    grouped[lv].push(id)
  }
  const maxLayer = Math.max(...Object.keys(grouped).map((k) => Number(k)), 0)
  const margin = 40
  const xStep = (width - margin * 2) / Math.max(1, maxLayer)
  const positions = ids.map((id) => {
    const lv = layer.get(id) || 0
    const col = grouped[lv]
    const idx = col.indexOf(id)
    const yStep = (height - margin * 2) / Math.max(1, col.length)
    const x = margin + lv * xStep
    const y = margin + (idx + 0.5) * yStep
    return { x, y, id }
  })
  const posMap = new Map<any, { x: number; y: number }>()
  positions.forEach((p, i) => posMap.set(ids[i], { x: p.x, y: p.y }))
  const lines = edges
    .map((e) => {
      const { s, t } = getEdgeEnds(e)
      const ps = posMap.get(s)
      const pt = posMap.get(t)
      if (!ps || !pt) return null
      return { x1: ps.x, y1: ps.y, x2: pt.x, y2: pt.y, type: e.type, sId: s, tId: t }
    })
    .filter(Boolean) as LayoutResult['lines']
  return { width, height, positions, lines }
}

function computeForceLayout(nodes: NodeLike[], edges: EdgeLike[], width = 900, height = 520): LayoutResult {
  // 初始放置：圆形
  const base = computeCircularLayout(nodes, edges, width, height)
  const positions = base.positions.map((p) => ({ ...p }))
  const ids = nodes.map((n, i) => (n.id ?? i))
  const idToIndex = new Map(ids.map((id, i) => [id, i]))
  // 简易力导：排斥 + 吸引
  const ITER = 100
  const kr = 8000 // 排斥系数
  const ka = 0.01 // 吸引系数
  const center = { x: width / 2, y: height / 2 }
  for (let it = 0; it < ITER; it++) {
    const fx = new Array(positions.length).fill(0)
    const fy = new Array(positions.length).fill(0)
    // 排斥
    for (let i = 0; i < positions.length; i++) {
      for (let j = i + 1; j < positions.length; j++) {
        const dx = positions[i].x - positions[j].x
        const dy = positions[i].y - positions[j].y
        const d2 = Math.max(0.01, dx * dx + dy * dy)
        const f = kr / d2
        const dist = Math.sqrt(d2)
        fx[i] += (dx / dist) * f
        fy[i] += (dy / dist) * f
        fx[j] -= (dx / dist) * f
        fy[j] -= (dy / dist) * f
      }
    }
    // 吸引（沿边）
    for (const e of edges) {
      const { s, t } = getEdgeEnds(e)
      const si = idToIndex.get(s)
      const ti = idToIndex.get(t)
      if (si == null || ti == null) continue
      const dx = positions[ti].x - positions[si].x
      const dy = positions[ti].y - positions[si].y
      fx[si] += dx * ka
      fy[si] += dy * ka
      fx[ti] -= dx * ka
      fy[ti] -= dy * ka
    }
    // 更新位置 + 轻微回中心
    for (let i = 0; i < positions.length; i++) {
      positions[i].x += fx[i] * 0.02 + (center.x - positions[i].x) * 0.001
      positions[i].y += fy[i] * 0.02 + (center.y - positions[i].y) * 0.001
      positions[i].x = Math.max(20, Math.min(width - 20, positions[i].x))
      positions[i].y = Math.max(20, Math.min(height - 20, positions[i].y))
    }
  }
  // 线段重算
  const idToPos = new Map(ids.map((id, i) => [id, { x: positions[i].x, y: positions[i].y }]))
  const lines = edges
    .map((e) => {
      const { s, t } = getEdgeEnds(e)
      const ps = idToPos.get(s)
      const pt = idToPos.get(t)
      if (!ps || !pt) return null
      return { x1: ps.x, y1: ps.y, x2: pt.x, y2: pt.y, type: e.type, sId: s, tId: t }
    })
    .filter(Boolean) as LayoutResult['lines']
  return { width, height, positions, lines }
}

const GraphWorkspacePage: React.FC = () => {
  const [jsonText, setJsonText] = useState('')
  const data = useMemo(() => {
    try {
      const obj = JSON.parse(jsonText)
      return obj
    } catch {
      return null
    }
  }, [jsonText])

  const nodes = useMemo(() => (Array.isArray((data as any)?.nodes) ? (data as any).nodes : []), [data])
  const edges = useMemo(() => (Array.isArray((data as any)?.edges) ? (data as any).edges : []), [data])

  const [layoutType, setLayoutType] = useState<'circular' | 'hierarchical' | 'force'>('circular')
  const [selectedNode, setSelectedNode] = useState<any>(null)
  const [scale, setScale] = useState(1)
  const [tx, setTx] = useState(0)
  const [ty, setTy] = useState(0)
  const dragRef = useRef<{ dragging: boolean; lastX: number; lastY: number }>({ dragging: false, lastX: 0, lastY: 0 })

  const layout = useMemo(() => {
    const w = 900, h = 520
    if (layoutType === 'hierarchical') return computeHierarchicalLayout(nodes as NodeLike[], edges as EdgeLike[], w, h)
    if (layoutType === 'force') return computeForceLayout(nodes as NodeLike[], edges as EdgeLike[], w, h)
    return computeCircularLayout(nodes as NodeLike[], edges as EdgeLike[], w, h)
  }, [nodes, edges, layoutType])
  const colorFor = (key: string | undefined) => {
    const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7f50', '#87cefa', '#d0ed57']
    if (!key) return '#999'
    const h = Math.abs(String(key).split('').reduce((acc, ch) => acc + ch.charCodeAt(0), 0))
    return colors[h % colors.length]
  }

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-4">
      <div>
        <h1 className="text-2xl font-bold">图谱工作台（最小版）</h1>
        <p className="text-sm text-muted-foreground mt-1">
          粘贴包含 `nodes` 与 `edges` 的 JSON 以查看基础统计；后续将集成查询与可视化。
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <div className="text-sm font-medium mb-2">输入图谱 JSON</div>
          <textarea className="border rounded px-2 py-2 w-full h-48" value={jsonText} onChange={(e) => setJsonText(e.target.value)} placeholder='{"nodes":[],"edges":[]}' />
        </div>
        <div>
          <GraphStatsPanel result={{ nodes, edges }} />
        </div>
      </div>

      {data && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="text-sm font-medium mb-2">节点（{nodes.length}）</div>
            <ul className="border rounded p-2 h-64 overflow-auto text-xs space-y-1">
              {nodes.map((n: any, idx: number) => (
                <li key={`n-${idx}`}>{JSON.stringify(n)}</li>
              ))}
            </ul>
          </div>
          <div>
            <div className="text-sm font-medium mb-2">关系（{edges.length}）</div>
            <ul className="border rounded p-2 h-40 overflow-auto text-xs space-y-1">
              {edges.map((e: any, idx: number) => (
                <li key={`e-${idx}`}>{JSON.stringify(e)}</li>
              ))}
            </ul>
            <div className="mt-3">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-medium">图可视化</div>
                <div className="flex items-center gap-2">
                  <label className="text-xs">布局</label>
                  <select className="border rounded px-2 py-1 text-xs" value={layoutType} onChange={(e) => setLayoutType(e.target.value as any)}>
                    <option value="circular">环形</option>
                    <option value="hierarchical">层级（DAG）</option>
                    <option value="force">力导</option>
                  </select>
                  <label className="text-xs ml-3">缩放</label>
                  <input type="range" min={50} max={200} value={Math.round(scale * 100)} onChange={(e) => setScale(Number(e.target.value) / 100)} />
                </div>
              </div>
              <div className="border rounded bg-muted" 
                   onWheel={(e) => { e.preventDefault(); const delta = e.deltaY < 0 ? 0.1 : -0.1; setScale((s) => Math.max(0.3, Math.min(3, s + delta))) }}
                   onMouseDown={(e) => { dragRef.current = { dragging: true, lastX: e.clientX, lastY: e.clientY } }}
                   onMouseMove={(e) => { const d = dragRef.current; if (!d.dragging) return; const dx = e.clientX - d.lastX; const dy = e.clientY - d.lastY; setTx((x) => x + dx); setTy((y) => y + dy); d.lastX = e.clientX; d.lastY = e.clientY }}
                   onMouseUp={() => { dragRef.current.dragging = false }}
                   onMouseLeave={() => { dragRef.current.dragging = false }}>
                <svg width={layout.width} height={layout.height} style={{ display: 'block', maxWidth: '100%' }}>
                  <defs>
                    <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
                    </marker>
                    <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
                      <feDropShadow dx="0" dy="0" stdDeviation="1" floodColor="#334155" floodOpacity="0.2" />
                    </filter>
                  </defs>
                  <g transform={`translate(${tx},${ty}) scale(${scale})`}>
                    {/* edges */}
                    {layout.lines.map((l, i) => {
                      const hl = selectedNode != null && (l.sId === selectedNode || l.tId === selectedNode)
                      return (
                        <line key={`l-${i}`} x1={l.x1} y1={l.y1} x2={l.x2} y2={l.y2}
                              stroke={hl ? '#ef4444' : colorFor(l.type)} strokeWidth={hl ? 2.5 : 1.5} opacity={0.9}
                              markerEnd="url(#arrow)" />
                      )
                    })}
                    {/* nodes */}
                    {(nodes as NodeLike[]).map((n, i) => {
                      const id = n.id ?? i
                      const selected = selectedNode === id
                      return (
                        <g key={`nsvg-${i}`} onClick={() => setSelectedNode(selected ? null : id)} style={{ cursor: 'pointer' }}>
                          <circle cx={layout.positions[i].x} cy={layout.positions[i].y} r={12} filter="url(#shadow)" fill={selected ? '#fbbf24' : '#4f46e5'} />
                          <text x={layout.positions[i].x + 14} y={layout.positions[i].y + 4} fontSize={12} fill="#334155">
                            {String(n.label ?? n.id ?? i)}
                          </text>
                        </g>
                      )
                    })}
                  </g>
                </svg>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default GraphWorkspacePage