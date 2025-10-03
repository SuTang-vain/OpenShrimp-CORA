/**
 * 全局类型定义
 * 定义应用中使用的所有类型接口
 */

// ============= 基础类型 =============

/**
 * API 响应基础类型
 */
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
  code?: number
}

/**
 * 分页参数
 */
export interface PaginationParams {
  page?: number
  limit?: number
  offset?: number
}

/**
 * 分页响应
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  hasMore: boolean
}

/**
 * 排序参数
 */
export interface SortParams {
  field: string
  order: 'asc' | 'desc'
}

/**
 * 过滤器类型
 */
export interface FilterParams {
  [key: string]: any
}

// ============= 用户相关类型 =============

/**
 * 用户信息
 */
export interface User {
  id: string
  username: string
  email: string
  avatar?: string
  role: UserRole
  createdAt: string
  updatedAt: string
  preferences?: UserPreferences
}

/**
 * 用户角色
 */
export enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
  GUEST = 'guest'
}

/**
 * 用户偏好设置
 */
export interface UserPreferences {
  theme: 'light' | 'dark' | 'system'
  language: string
  searchSettings: SearchPreferences
  documentSettings: DocumentPreferences
}

/**
 * 搜索偏好设置
 */
export interface SearchPreferences {
  defaultStrategy: SearchStrategy
  resultsPerPage: number
  enableAutoComplete: boolean
  enableSearchHistory: boolean
}

/**
 * 文档偏好设置
 */
export interface DocumentPreferences {
  defaultChunkingStrategy: ChunkingStrategy
  defaultChunkSize: number
  autoProcess: boolean
  enableOCR: boolean
}

/**
 * 认证相关类型
 */
export interface AuthState {
  isAuthenticated: boolean
  user: User | null
  token: string | null
  refreshToken: string | null
}

export interface LoginRequest {
  username: string
  password: string
  rememberMe?: boolean
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  confirmPassword: string
}

// ============= 搜索相关类型 =============

/**
 * 搜索策略
 */
export enum SearchStrategy {
  SIMILARITY = 'similarity',
  HYBRID = 'hybrid',
  MMR = 'mmr',
  KEYWORD = 'keyword',
  SEMANTIC_HYBRID = 'semantic_hybrid'
}

/**
 * 搜索请求
 */
export interface SearchRequest {
  query: string
  strategy?: SearchStrategy
  topK?: number
  filters?: FilterParams
  threshold?: number
  includeMetadata?: boolean
}

/**
 * 搜索结果项
 */
export interface SearchResultItem {
  id: string
  content: string
  score: number
  rank: number
  docId: string
  chunkId: string
  source?: string
  title?: string
  url?: string
  metadata?: Record<string, any>
  highlight?: string
}

/**
 * 搜索响应
 */
export interface SearchResponse {
  query: string
  results: SearchResultItem[]
  total: number
  executionTime: number
  strategy: SearchStrategy
  suggestions?: SearchSuggestion[]
}

/**
 * RAG 查询请求
 */
export interface RAGQueryRequest {
  query: string
  strategy?: SearchStrategy
  topK?: number
  includeContext?: boolean
  maxTokens?: number
}

/**
 * RAG 查询响应
 */
export interface RAGQueryResponse {
  query: string
  answer: string
  sources: RetrievedChunk[]
  confidence: number
  executionTime: number
}

/**
 * 检索到的文档块
 */
export interface RetrievedChunk {
  chunkId: string
  docId: string
  content: string
  score: number
  metadata?: Record<string, any>
}

/**
 * 搜索建议
 */
export interface SearchSuggestion {
  text: string
  score: number
  type: 'query_completion' | 'entity' | 'topic' | 'generic_expansion'
  metadata?: Record<string, any>
}

/**
 * 搜索历史项
 */
export interface SearchHistoryItem {
  id: string
  query: string
  timestamp: string
  strategy: SearchStrategy
  resultsCount: number
  executionTime: number
  userRating?: number
}

/**
 * 搜索统计
 */
export interface SearchStats {
  totalQueries: number
  successfulQueries: number
  failedQueries: number
  avgExecutionTime: number
  popularQueries: Record<string, number>
  strategyUsage: Record<string, number>
}

// ============= 文档相关类型 =============

/**
 * 文档状态
 */
export enum DocumentStatus {
  UPLOADED = 'uploaded',
  PROCESSING = 'processing',
  PROCESSED = 'processed',
  FAILED = 'failed',
  DELETED = 'deleted'
}

/**
 * 文档类型
 */
export enum DocumentType {
  TEXT = 'text',
  PDF = 'pdf',
  WORD = 'word',
  HTML = 'html',
  JSON = 'json',
  CSV = 'csv',
  MARKDOWN = 'markdown',
  OTHER = 'other'
}

/**
 * 分块策略
 */
export enum ChunkingStrategy {
  FIXED_SIZE = 'fixed_size',
  SENTENCE = 'sentence',
  PARAGRAPH = 'paragraph',
  SEMANTIC = 'semantic',
  RECURSIVE = 'recursive'
}

/**
 * 文档信息
 */
export interface DocumentInfo {
  id: string
  filename: string
  originalFilename: string
  contentType: string
  fileSize: number
  uploadTime: string
  status: DocumentStatus
  chunksCount: number
  processingTime?: number
  userId?: string
  metadata?: Record<string, any>
  tags?: string[]
  language?: string
  errorMessage?: string
}

/**
 * 文档上传请求
 */
export interface DocumentUploadRequest {
  file: File
  metadata?: Record<string, any>
  tags?: string[]
  language?: string
  autoProcess?: boolean
}

/**
 * 文档处理请求
 */
export interface DocumentProcessRequest {
  chunkingStrategy: ChunkingStrategy
  chunkSize: number
  chunkOverlap: number
  forceReprocess?: boolean
}

/**
 * 文档处理结果
 */
export interface ProcessingResult {
  docId: string
  status: 'success' | 'failed' | 'already_processed'
  chunksCreated: number
  processingTime: number
  message: string
  errorDetails?: Record<string, any>
}

/**
 * 文档块
 */
export interface DocumentChunk {
  id: string
  docId: string
  content: string
  chunkIndex: number
  startChar: number
  endChar: number
  metadata?: Record<string, any>
}

/**
 * 文档统计
 */
export interface DocumentStats {
  totalDocuments: number
  totalChunks: number
  totalSize: number
  processingSuccess: number
  processingFailed: number
  avgProcessingTime: number
  formatDistribution: Record<string, number>
  statusDistribution: Record<string, number>
}

// ============= UI 相关类型 =============

/**
 * 主题类型
 */
export type Theme = 'light' | 'dark' | 'system'

/**
 * 通知类型
 */
export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
  actions?: NotificationAction[]
}

/**
 * 通知操作
 */
export interface NotificationAction {
  label: string
  action: () => void
  variant?: 'default' | 'destructive'
}

/**
 * 模态框状态
 */
export interface ModalState {
  isOpen: boolean
  title?: string
  content?: React.ReactNode
  onConfirm?: () => void
  onCancel?: () => void
  confirmText?: string
  cancelText?: string
  variant?: 'default' | 'destructive'
}

/**
 * 加载状态
 */
export interface LoadingState {
  isLoading: boolean
  message?: string
  progress?: number
}

/**
 * 表单字段类型
 */
export interface FormField {
  name: string
  label: string
  type: 'text' | 'email' | 'password' | 'number' | 'select' | 'textarea' | 'file' | 'checkbox'
  placeholder?: string
  required?: boolean
  validation?: ValidationRule[]
  options?: SelectOption[]
}

/**
 * 选择选项
 */
export interface SelectOption {
  value: string | number
  label: string
  disabled?: boolean
}

/**
 * 验证规则
 */
export interface ValidationRule {
  type: 'required' | 'email' | 'minLength' | 'maxLength' | 'pattern' | 'custom'
  value?: any
  message: string
}

// ============= 配置相关类型 =============

/**
 * 应用配置
 */
export interface AppConfig {
  apiBaseUrl: string
  version: string
  environment: 'development' | 'production' | 'test'
  features: FeatureFlags
  limits: AppLimits
}

/**
 * 功能开关
 */
export interface FeatureFlags {
  enableRAG: boolean
  enableOCR: boolean
  enableWebSearch: boolean
  enableDocumentUpload: boolean
  enableUserRegistration: boolean
  enableAnalytics: boolean
}

/**
 * 应用限制
 */
export interface AppLimits {
  maxFileSize: number
  maxFilesPerUpload: number
  maxSearchResults: number
  maxSearchHistory: number
  rateLimitPerMinute: number
}

// ============= 错误相关类型 =============

/**
 * 错误类型
 */
export interface AppError {
  code: string
  message: string
  details?: any
  timestamp: string
  stack?: string
}

/**
 * 错误边界状态
 */
export interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
  errorInfo?: React.ErrorInfo
}

// ============= 事件相关类型 =============

/**
 * 应用事件
 */
export type AppEvent =
  | { type: 'SEARCH_PERFORMED'; payload: { query: string; results: number } }
  | { type: 'DOCUMENT_UPLOADED'; payload: { docId: string; filename: string } }
  | { type: 'DOCUMENT_PROCESSED'; payload: { docId: string; chunksCount: number } }
  | { type: 'USER_LOGIN'; payload: { userId: string } }
  | { type: 'USER_LOGOUT'; payload: { userId: string } }
  | { type: 'ERROR_OCCURRED'; payload: { error: AppError } }

// ============= 工具类型 =============

/**
 * 深度部分类型
 */
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

/**
 * 可选字段类型
 */
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

/**
 * 必需字段类型
 */
export type Required<T, K extends keyof T> = T & { [P in K]-?: T[P] }

/**
 * 键值对类型
 */
export type KeyValuePair<T = any> = {
  key: string
  value: T
}

/**
 * 异步状态类型
 */
export type AsyncState<T> = {
  data: T | null
  loading: boolean
  error: string | null
}

/**
 * 回调函数类型
 */
export type Callback<T = void> = () => T
export type AsyncCallback<T = void> = () => Promise<T>
export type CallbackWithParam<P, T = void> = (param: P) => T
export type AsyncCallbackWithParam<P, T = void> = (param: P) => Promise<T>