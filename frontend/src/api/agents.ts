import { apiClient } from './client'
import type { ApiResponse } from '@/types'

export interface GraphNode {
  id: string
  label?: string
}

export interface GraphEdge {
  source: string
  target: string
  label?: string
}

export interface GraphRAGRequest {
  query: string
  top_k?: number
  depth?: number
  mode?: 'neighbors' | 'shortest_path'
  shortest_a?: string | null
  shortest_b?: string | null
  max_context_tokens?: number
}

export interface GraphRAGResponse {
  answer: string
  graph_source: string
  graph: {
    nodes: GraphNode[]
    edges: GraphEdge[]
  }
  terms: string[]
  retrieved_count: number
}

class AgentsApi {
  async graphRag(params: GraphRAGRequest): Promise<ApiResponse<GraphRAGResponse>> {
    // 前端默认 baseURL 为 `/api`，此处应调用 `/api/v1/agents/graph-rag`
    return await apiClient.post<GraphRAGResponse>('/v1/agents/graph-rag', params)
  }
}

const agentsApi = new AgentsApi()
export { agentsApi }
export default agentsApi
export type { AgentsApi }