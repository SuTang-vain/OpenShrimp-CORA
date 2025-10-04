import * as React from 'react'
import { useEffect, useRef, useState } from 'react'
import cytoscape, { Core } from 'cytoscape'
import { Sparkles, Network, Play, RefreshCcw, Info, Settings, Download, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'

import { agentsApi, type GraphRAGRequest, type GraphNode, type GraphEdge } from '@/api/agents'
import { cn } from '@/utils/cn'
import { useConfigStore } from '@/stores/configStore'
import { ServiceType, ServiceStatus } from '@/types/services'

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

const defaultRequest: GraphRAGRequest = {
  query: '知识图谱如何用于检索增强生成？',
  top_k: 6,
  depth: 1,
  mode: 'neighbors',
  shortest_a: null,
  shortest_b: null,
  max_context_tokens: 800,
}

const GraphWorkbenchPage: React.FC = () => {
  const cyRef = useRef<HTMLDivElement | null>(null)
  const cyInstance = useRef<Core | null>(null)

  const [form, setForm] = useState<GraphRAGRequest>(defaultRequest)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [answer, setAnswer] = useState<string>('')
  const [terms, setTerms] = useState<string[]>([])
  const [graphSource, setGraphSource] = useState<string>('none')
  const [graph, setGraph] = useState<GraphData>({ nodes: [], edges: [] })
  const [isFullscreen, setIsFullscreen] = useState(false)

  // 图谱服务（Neo4j）配置检测
  const { services } = useConfigStore()
  const kgService = (services || []).find((s) => s.type === ServiceType.KNOWLEDGE_GRAPH)
  const isKgConfigured = !!kgService
  const isKgConnected = kgService?.status === ServiceStatus.CONNECTED

  useEffect(() => {
    if (!cyRef.current) return
    if (!cyInstance.current) {
      cyInstance.current = cytoscape({
        container: cyRef.current,
        style: [
          { 
            selector: 'node', 
            style: { 
              'background-color': '#60a5fa', 
              label: 'data(label)', 
              color: '#111827', 
              'font-size': '14px', 
              'text-outline-color': '#f3f4f6', 
              'text-outline-width': 2,
              'width': '60px',
              'height': '60px',
              'border-width': 2,
              'border-color': '#3b82f6',
              'text-valign': 'center',
              'text-halign': 'center'
            } 
          },
          { 
            selector: 'edge', 
            style: { 
              'line-color': '#94a3b8', 
              'width': 3, 
              'target-arrow-shape': 'triangle', 
              'target-arrow-color': '#94a3b8', 
              'curve-style': 'bezier',
              'opacity': 0.8
            } 
          },
          { 
            selector: '.term', 
            style: { 
              'background-color': '#22d3ee', 
              'border-color': '#0891b2', 
              'border-width': 3,
              'width': '70px',
              'height': '70px'
            } 
          },
          { 
            selector: '.highlight', 
            style: { 
              'line-color': '#f59e0b', 
              'target-arrow-color': '#f59e0b', 
              'width': 4,
              'opacity': 1
            } 
          },
          {
            selector: 'node:selected',
            style: {
              'border-color': '#ef4444',
              'border-width': 4
            }
          }
        ],
        layout: { 
          name: 'concentric', 
          minNodeSpacing: 50, 
          concentric: (n) => (n.hasClass('term') ? 2 : 1), 
          levelWidth: () => 3,
          animate: true,
          animationDuration: 500
        },
        wheelSensitivity: 0.2,
        userZoomingEnabled: true,
        userPanningEnabled: true,
      })

      // 添加节点点击事件
      cyInstance.current.on('tap', 'node', function(evt) {
        const node = evt.target
        console.log('节点被点击:', node.data())
      })
    }
  }, [])

  const renderGraph = (data: GraphData, termList: string[]) => {
    const cy = cyInstance.current
    if (!cy) return
    cy.elements().remove()
    const nodes = (data.nodes || []).map((n) => ({ 
      data: { id: n.id, label: n.label || n.id }, 
      classes: termList.includes((n.label || n.id).toLowerCase()) ? 'term' : '' 
    }))
    const edges = (data.edges || []).map((e) => ({ 
      data: { id: `${e.source}->${e.target}`, source: e.source, target: e.target }, 
      classes: 'highlight' 
    }))
    cy.add([...nodes, ...edges])
    cy.layout({ 
      name: 'concentric', 
      minNodeSpacing: 50,
      animate: true,
      animationDuration: 800
    }).run()
    cy.fit(undefined, 50)
  }

  const runGraphRag = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await agentsApi.graphRag(form)
      if (!res.success || !res.data) {
        setError((res as any).error || '请求失败')
        setLoading(false)
        return
      }
      const d = res.data
      setAnswer(d.answer)
      setTerms(d.terms || [])
      setGraphSource(d.graph_source || 'none')
      const g = d.graph || { nodes: [], edges: [] }
      setGraph(g)
      renderGraph(g, (d.terms || []).map((t) => t.toLowerCase()))
    } catch (e: any) {
      setError(e?.error || e?.message || '请求失败')
    } finally {
      setLoading(false)
    }
  }

  const handleZoomIn = () => {
    const cy = cyInstance.current
    if (cy) cy.zoom(cy.zoom() * 1.2)
  }

  const handleZoomOut = () => {
    const cy = cyInstance.current
    if (cy) cy.zoom(cy.zoom() * 0.8)
  }

  const handleFitView = () => {
    const cy = cyInstance.current
    if (cy) cy.fit(undefined, 50)
  }

  const handleExportGraph = () => {
    const cy = cyInstance.current
    if (cy) {
      const png = cy.png({ scale: 2, full: true })
      const link = document.createElement('a')
      link.download = 'graph-export.png'
      link.href = png
      link.click()
    }
  }

  return (
    <div className={cn('min-h-[80vh]', isFullscreen && 'fixed inset-0 z-50 bg-background')}> 
      {/* 页面头部 */}
      <div className="bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20 border rounded-xl p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-primary/10 rounded-xl">
              <Network className="h-8 w-8 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                图谱工作台
              </h1>
              <p className="text-muted-foreground mt-1 text-lg">
                基于 GraphRAG 的智能知识图谱分析平台
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <div className="px-3 py-1 bg-primary/10 rounded-full">
              <span className="text-xs font-medium text-primary">
                数据源: {graphSource || 'none'}
              </span>
            </div>
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-2 hover:bg-muted rounded-lg transition-colors"
              title={isFullscreen ? "退出全屏" : "全屏模式"}
            >
              <Maximize2 className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* 配置缺失提示 */}
      {(!isKgConfigured || !isKgConnected) && (
        <div className="mx-6 mb-4 bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <Info className="h-5 w-5 text-amber-600 mt-0.5" />
            <div className="text-amber-800">
              <p className="font-medium">图谱服务未完成配置或未连接，部分功能不可用。</p>
              <p className="text-sm mt-1 text-amber-700">请前往“服务配置”页完成 Neo4j（Aura 或本地）配置，并测试连通性。</p>
              <div className="mt-3">
                <a href="/services" className="btn btn-outline btn-sm">前往服务配置</a>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className={cn(
        "grid gap-6",
        isFullscreen ? "grid-cols-1 lg:grid-cols-4 h-[calc(100vh-140px)]" : "grid-cols-1 lg:grid-cols-3"
      )}>
        {/* 左侧：控制面板 */}
        <div className={cn("space-y-4", isFullscreen && "lg:col-span-1")}>
          {/* 查询配置 */}
          <div className="card p-5 space-y-4">
            <div className="flex items-center space-x-2 mb-4">
              <Settings className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">查询配置</h3>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">查询内容</label>
              <textarea
                className="w-full border rounded-lg p-3 bg-background resize-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
                rows={4}
                placeholder="输入您的问题，例如：GraphRAG 如何结合上下文图谱？"
                value={form.query}
                onChange={(e) => setForm((f) => ({ ...f, query: e.target.value }))}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium mb-1">检索模式</label>
                <select
                  className="w-full border rounded-lg p-2 bg-background focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
                  value={form.mode}
                  onChange={(e) => setForm((f) => ({ ...f, mode: e.target.value as any }))}
                >
                  <option value="neighbors">邻居节点</option>
                  <option value="shortest">最短路径</option>
                  <option value="subgraph">子图</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">返回数量</label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  className="w-full border rounded-lg p-2 bg-background focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
                  value={form.top_k}
                  onChange={(e) => setForm((f) => ({ ...f, top_k: Number(e.target.value) }))}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium mb-1">搜索深度</label>
                <input
                  type="number"
                  min="1"
                  max="5"
                  className="w-full border rounded-lg p-2 bg-background focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
                  value={form.depth}
                  onChange={(e) => setForm((f) => ({ ...f, depth: Number(e.target.value) }))}
                />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">上下文长度</label>
                <input
                  type="number"
                  min="100"
                  max="2000"
                  step="100"
                  className="w-full border rounded-lg p-2 bg-background focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
                  value={form.max_context_tokens}
                  onChange={(e) => setForm((f) => ({ ...f, max_context_tokens: Number(e.target.value) }))}
                />
              </div>
            </div>

            {form.mode === 'shortest' && (
              <div className="grid grid-cols-2 gap-3 p-3 bg-muted/30 rounded-lg">
                <div>
                  <label className="block text-xs font-medium mb-1">起点节点</label>
                  <input
                    type="text"
                    className="w-full border rounded-lg p-2 bg-background focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
                    placeholder="输入起点"
                    value={form.shortest_a || ''}
                    onChange={(e) => setForm((f) => ({ ...f, shortest_a: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">终点节点</label>
                  <input
                    type="text"
                    className="w-full border rounded-lg p-2 bg-background focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
                    placeholder="输入终点"
                    value={form.shortest_b || ''}
                    onChange={(e) => setForm((f) => ({ ...f, shortest_b: e.target.value }))}
                  />
                </div>
              </div>
            )}

            <div className="flex items-center space-x-2 pt-2">
              <button 
                disabled={loading} 
                onClick={runGraphRag} 
                className="flex-1 btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
                    分析中...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" /> 
                    运行分析
                  </>
                )}
              </button>
              <button
                disabled={loading}
                onClick={() => {
                  setForm(defaultRequest)
                  setAnswer('')
                  setGraph({ nodes: [], edges: [] })
                  setTerms([])
                  setGraphSource('none')
                  setError(null)
                  const cy = cyInstance.current
                  cy?.elements().remove()
                }}
                className="btn btn-outline"
                title="重置所有设置"
              >
                <RefreshCcw className="h-4 w-4" />
              </button>
            </div>

            {error && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Info className="h-4 w-4 text-destructive" />
                  <p className="text-destructive text-sm font-medium">错误</p>
                </div>
                <p className="text-destructive text-sm mt-1">{error}</p>
              </div>
            )}
          </div>

          {/* 分析结果 */}
          <div className="card p-5">
            <div className="flex items-center space-x-2 mb-4">
              <Sparkles className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">分析结果</h3>
            </div>
            
            <div className="space-y-4">
              <div className="prose prose-sm max-w-none">
                <div className="p-3 bg-muted/30 rounded-lg min-h-[100px]">
                  {answer ? (
                    <div className="whitespace-pre-wrap text-sm leading-relaxed">{answer}</div>
                  ) : (
                    <div className="text-muted-foreground text-sm italic">
                      运行分析后，这里将显示 AI 生成的回答...
                    </div>
                  )}
                </div>
              </div>
              
              {terms.length > 0 && (
                <div>
                  <div className="text-xs font-medium text-muted-foreground mb-2">关键术语</div>
                  <div className="flex flex-wrap gap-2">
                    {terms.map((t) => (
                      <span 
                        key={t} 
                        className="px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium border border-primary/20"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {graph.nodes.length > 0 && (
                <div className="text-xs text-muted-foreground pt-2 border-t">
                  图谱统计: {graph.nodes.length} 个节点, {graph.edges.length} 条边
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 右侧：图可视化 */}
        <div className={cn("space-y-4", isFullscreen ? "lg:col-span-3" : "lg:col-span-2")}>
          <div className="card p-4">
            {/* 图控制工具栏 */}
            <div className="flex items-center justify-between mb-4 pb-3 border-b">
              <h3 className="font-semibold flex items-center space-x-2">
                <Network className="h-5 w-5 text-primary" />
                <span>知识图谱可视化</span>
              </h3>
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleZoomIn}
                  className="p-2 hover:bg-muted rounded-lg transition-colors"
                  title="放大"
                >
                  <ZoomIn className="h-4 w-4" />
                </button>
                <button
                  onClick={handleZoomOut}
                  className="p-2 hover:bg-muted rounded-lg transition-colors"
                  title="缩小"
                >
                  <ZoomOut className="h-4 w-4" />
                </button>
                <button
                  onClick={handleFitView}
                  className="p-2 hover:bg-muted rounded-lg transition-colors"
                  title="适应视图"
                >
                  <Maximize2 className="h-4 w-4" />
                </button>
                <button
                  onClick={handleExportGraph}
                  className="p-2 hover:bg-muted rounded-lg transition-colors"
                  title="导出图片"
                  disabled={graph.nodes.length === 0}
                >
                  <Download className="h-4 w-4" />
                </button>
              </div>
            </div>
            
            {/* 图容器 */}
            <div className={cn(
              "rounded-lg border bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-blue-950 relative overflow-hidden",
              isFullscreen ? "h-[calc(100vh-220px)]" : "h-[600px]"
            )}>
              <div ref={cyRef} className="w-full h-full" />
              
              {graph.nodes.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center space-y-3">
                    <Network className="h-16 w-16 text-muted-foreground/30 mx-auto" />
                    <div>
                      <p className="text-muted-foreground font-medium">暂无图谱数据</p>
                      <p className="text-muted-foreground/70 text-sm">运行分析后，知识图谱将在此处显示</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* 图例说明 */}
            {graph.nodes.length > 0 && (
              <div className="mt-4 p-3 bg-muted/30 rounded-lg">
                <div className="text-xs font-medium text-muted-foreground mb-2">图例说明</div>
                <div className="flex items-center space-x-6 text-xs">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full bg-blue-400 border-2 border-blue-600"></div>
                    <span>普通节点</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full bg-cyan-400 border-2 border-cyan-600"></div>
                    <span>关键术语</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-0.5 bg-amber-500"></div>
                    <span>关联边</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default GraphWorkbenchPage