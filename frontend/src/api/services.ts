import { apiClient } from './client'

// 服务提供方类型
export interface ServiceProvider {
  id: string
  name: string
  type: string
  description?: string
}

// 保存凭据的请求载荷
export interface CredentialsPayload {
  provider_id: string
  credentials: Record<string, string | undefined>
}

// 连通性测试结果
export interface ConnectivityStatus {
  reachable: boolean
  message?: string
  details?: Record<string, any>
}

const servicesApi = {
  // 获取服务提供商列表
  async listProviders() {
    return apiClient.get<ServiceProvider[]>('/services/providers')
  },

  // 保存服务凭据
  async saveCredentials(payload: CredentialsPayload) {
    return apiClient.post<{ saved: boolean }>('/services/credentials', payload)
  },

  // 测试服务连通性
  async testConnectivity(providerId: string) {
    return apiClient.get<ConnectivityStatus>('/services/test', {
      params: { provider_id: providerId },
    } as any)
  },
}

export default servicesApi
export { servicesApi }