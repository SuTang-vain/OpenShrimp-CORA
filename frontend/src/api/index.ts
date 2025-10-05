/**
 * API 模块统一导出
 * 提供所有 API 服务的统一入口
 */

// 导出 API 客户端
export { apiClient, ApiClient } from './client'
export type { ApiClientConfig } from './client'

// 导入API客户端
import { apiClient } from './client'

// 导入各个API模块
import authApi from './auth'
import searchApi from './search'
import documentsApi from './documents'
import settingsApi from './settings'
import agentsApi from './agents'
import servicesApi from './services'

// 导出认证 API
export { authApi }
export * from './auth'

// 导出搜索 API
export { searchApi }
export * from './search'

// 导出文档 API
export { documentsApi }
export * from './documents'

// 导出设置 API
export { settingsApi }
export * from './settings'

// 导出智能体 API
export { agentsApi }
export * from './agents'

// 导出服务适配 API
export { servicesApi }
export * from './services'

// 统一的 API 对象
export const api = {
  auth: authApi,
  search: searchApi,
  documents: documentsApi,
  settings: settingsApi,
  agents: agentsApi,
  services: servicesApi,
  client: apiClient,
} as const

// 默认导出
export default api