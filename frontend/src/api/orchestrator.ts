import { ApiClient } from './client'

const getOrchestratorBaseUrl = () => {
  const v = (import.meta as any).env.VITE_ORCH_BASE_URL
  if (!v || String(v).trim() === '') return 'http://localhost:8003'
  return v
}

export const orchestratorClient = new ApiClient({ baseURL: getOrchestratorBaseUrl() })

export async function getTasks() {
  const res = await orchestratorClient.get('/orchestrator/tasks')
  if (res.success) return res.data
  throw new Error(res.error || '获取任务列表失败')
}

export async function startTask(params: { task: string; input: any }) {
  const res = await orchestratorClient.post('/orchestrator/tasks/start', params)
  if (res.success) return res.data
  throw new Error(res.error || '启动任务失败')
}

export async function getTaskStatus(tid: string) {
  const res = await orchestratorClient.get(`/orchestrator/tasks/${tid}/status`)
  if (res.success) return res.data
  throw new Error(res.error || '获取任务状态失败')
}

export async function getTaskArtifact(tid: string) {
  const res = await orchestratorClient.get(`/orchestrator/tasks/${tid}/artifact`)
  if (res.success) return res.data
  throw new Error(res.error || '获取任务产出失败')
}