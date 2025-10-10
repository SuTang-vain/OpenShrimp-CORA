import React, { useEffect, useState } from 'react'
import { getTools, invokeTool, StrataToolDef } from '@/api/strata'
import { SchemaFormRenderer } from '@/lib/schema-form'
import { generateTraceId, nowIso } from '@/lib/trace'

interface InvocationResult {
  tool: string
  success: boolean
  result?: any
  error?: string
}

export const ToolDiscoveryPanel: React.FC = () => {
  const [tools, setTools] = useState<StrataToolDef[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<StrataToolDef | null>(null)
  const [invoking, setInvoking] = useState(false)
  const [invocationResult, setInvocationResult] = useState<InvocationResult | null>(null)

  useEffect(() => {
    const fetchTools = async () => {
      try {
        setLoading(true)
        const data = await getTools()
        setTools(data.tools || [])
      } catch (e: any) {
        setError(e?.message || '加载工具失败')
      } finally {
        setLoading(false)
      }
    }
    fetchTools()
  }, [])

  const handleSubmit = async (values: Record<string, any>) => {
    if (!selected) return
    try {
      setInvoking(true)
      setInvocationResult(null)
      const traceId = generateTraceId()
      const res = await invokeTool({ tool: selected.name, input: values, trace_id: traceId })
      setInvocationResult({ tool: selected.name, success: true, result: res })
    } catch (e: any) {
      setInvocationResult({ tool: selected.name, success: false, error: e?.message || '调用失败' })
    } finally {
      setInvoking(false)
    }
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Strata 工具发现</h2>
        <div className="text-xs text-muted-foreground">{nowIso()}</div>
      </div>

      {loading && <div className="text-sm text-muted-foreground">正在加载工具列表...</div>}
      {error && <div className="text-sm text-destructive">{error}</div>}

      {!loading && tools.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {tools.map((t) => (
            <button
              key={t.name}
              className={`border rounded p-3 text-left hover:bg-accent ${selected?.name === t.name ? 'bg-accent border-primary' : ''}`}
              onClick={() => setSelected(t)}
            >
              <div className="font-medium">{t.name}</div>
              <div className="text-xs text-muted-foreground">{t.description}</div>
            </button>
          ))}
        </div>
      )}

      {selected && (
        <div className="mt-4">
          <h3 className="text-base font-semibold mb-2">参数配置（{selected.name}）</h3>
          <SchemaFormRenderer schema={selected.schema as any} onSubmit={handleSubmit} submitLabel={invoking ? '执行中...' : '执行工具'} />
        </div>
      )}

      {invocationResult && (
        <div className="mt-4">
          <h3 className="text-base font-semibold mb-2">调用结果</h3>
          {!invocationResult.success ? (
            <div className="text-sm text-destructive">{invocationResult.error}</div>
          ) : (
            <pre className="text-xs border rounded p-3 overflow-auto max-h-96 bg-muted">
              {JSON.stringify(invocationResult.result, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  )}

export default ToolDiscoveryPanel