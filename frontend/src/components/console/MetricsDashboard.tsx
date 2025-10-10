import { useEffect, useState } from 'react'
import { getMetrics } from '@/api/strata'

type ToolMetrics = {
  count: number
  success: number
  failure: number
  avg_latency_ms: number
}

export default function MetricsDashboard() {
  const [metrics, setMetrics] = useState<any | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    try {
      setLoading(true)
      const data = await getMetrics()
      setMetrics(data)
    } catch (e: any) {
      setError(e?.message || '加载指标失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    const t = setInterval(load, 5000)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Strata 指标</h2>
        <button className="text-xs underline decoration-dotted" onClick={load} disabled={loading}>
          刷新
        </button>
      </div>
      {loading && <div className="text-sm text-muted-foreground">加载中...</div>}
      {error && <div className="text-sm text-destructive">{error}</div>}
      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
          <div className="border rounded p-3">
            <div className="text-xs text-muted-foreground">调用总数</div>
            <div className="text-xl font-semibold">{metrics.total}</div>
          </div>
          <div className="border rounded p-3">
            <div className="text-xs text-muted-foreground">成功率</div>
            <div className="text-xl font-semibold">{Number(metrics.success_rate || 0).toFixed(1)}%</div>
          </div>
          <div className="border rounded p-3">
            <div className="text-xs text-muted-foreground">平均时延</div>
            <div className="text-xl font-semibold">{Number(metrics.avg_latency_ms || 0).toFixed(1)} ms</div>
          </div>
          <div className="border rounded p-3">
            <div className="text-xs text-muted-foreground">失败数</div>
            <div className="text-xl font-semibold">{metrics.failure}</div>
          </div>
        </div>
      )}
      {metrics?.tools && Object.keys(metrics.tools).length > 0 && (
        <div className="mt-4">
          <div className="text-sm font-medium mb-2">按工具</div>
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {Object.entries(metrics.tools as Record<string, ToolMetrics>).map(([name, tm]) => (
              <li key={name} className="border rounded p-3 text-sm flex justify-between">
                <div>
                  <div className="font-medium">{name}</div>
                  <div className="text-xs text-muted-foreground">count {tm.count} / success {tm.success} / failure {tm.failure}</div>
                </div>
                <div className="text-xs">{Number(tm.avg_latency_ms || 0).toFixed(1)} ms</div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}