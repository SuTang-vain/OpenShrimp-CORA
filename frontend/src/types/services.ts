/**
 * 服务配置相关类型定义
 */

/**
 * 服务类型枚举
 */
export enum ServiceType {
  LLM = 'llm',
  WEB_CRAWLER = 'web_crawler',
  KNOWLEDGE_GRAPH = 'knowledge_graph',
  LOCAL_MODEL = 'local_model'
}

/**
 * 服务状态枚举
 */
export enum ServiceStatus {
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  TESTING = 'testing',
  ERROR = 'error'
}

/**
 * 基础服务配置接口
 */
export interface BaseServiceConfig {
  id: string
  name: string
  type: ServiceType
  description: string
  officialUrl: string
  enabled: boolean
  status: ServiceStatus
  lastTested?: Date
  errorMessage?: string
}

/**
 * LLM服务配置
 */
export interface LLMServiceConfig extends BaseServiceConfig {
  type: ServiceType.LLM
  apiKey: string
  baseUrl?: string
  model?: string
  maxTokens?: number
  temperature?: number
}

/**
 * 网页爬取服务配置
 */
export interface WebCrawlerServiceConfig extends BaseServiceConfig {
  type: ServiceType.WEB_CRAWLER
  apiKey: string
  baseUrl?: string
  maxPages?: number
  timeout?: number
}

/**
 * 知识图谱数据库服务配置
 */
export interface KnowledgeGraphServiceConfig extends BaseServiceConfig {
  type: ServiceType.KNOWLEDGE_GRAPH
  connectionUrl: string
  username?: string
  password?: string
  database?: string
  authType: 'basic' | 'token'
  apiKey?: string
}

/**
 * 本地模型服务配置
 */
export interface LocalModelServiceConfig extends BaseServiceConfig {
  type: ServiceType.LOCAL_MODEL
  baseUrl: string
  healthCheckUrl?: string
  apiKey?: string
  models?: string[]
}

/**
 * 联合服务配置类型
 */
export type ServiceConfig = 
  | LLMServiceConfig 
  | WebCrawlerServiceConfig 
  | KnowledgeGraphServiceConfig 
  | LocalModelServiceConfig

/**
 * 服务配置表单数据
 */
export interface ServiceConfigFormData {
  name: string
  description: string
  enabled: boolean
  apiKey?: string
  baseUrl?: string
  connectionUrl?: string
  username?: string
  password?: string
  authType?: 'basic' | 'token'
  model?: string
  maxTokens?: number
  temperature?: number
  maxPages?: number
  timeout?: number
  database?: string
  healthCheckUrl?: string
}

/**
 * 服务测试结果
 */
export interface ServiceTestResult {
  success: boolean
  message: string
  responseTime?: number
  details?: Record<string, any>
}

/**
 * 预定义服务模板
 */
export interface ServiceTemplate {
  id: string
  name: string
  type: ServiceType
  description: string
  officialUrl: string
  setupInstructions: string[]
  defaultConfig: Partial<ServiceConfigFormData>
  requiredFields: string[]
  optionalFields: string[]
  icon?: string
  tags?: string[]
}