import { ApiClient } from './client'

const getStrataBaseUrl = () => {
  const v = (import.meta as any).env.VITE_STRATA_BASE_URL
  if (!v || String(v).trim() === '') return 'http://localhost:8080'
  return v
}

export const strataClient = new ApiClient({ baseURL: getStrataBaseUrl() })

export interface StrataToolDef {
  name: string
  description: string
  schema: any
}

export async function getTools(): Promise<{ tools: StrataToolDef[] }> {
  const res = await strataClient.get<{ tools: StrataToolDef[] }>('/tools')
  if (res.success) return res.data as any
  throw new Error(res.error || '获取工具失败')
}

export async function invokeTool(params: { tool: string; input: any; trace_id?: string }) {
  const payload = { tool: params.tool, input: { ...params.input, trace_id: params.trace_id } }
  const res = await strataClient.post('/invoke', payload)
  if (res.success) return res.data
  throw new Error(res.error || '调用工具失败')
}

export async function getMetrics(): Promise<any> {
  const res = await strataClient.get('/metrics')
  if (res.success) return res.data
  throw new Error(res.error || '获取指标失败')
}