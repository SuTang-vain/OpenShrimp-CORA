import { apiClient } from './client'
import type { ApiResponse } from '@/types'

/**
 * 用户设置数据结构
 */
export interface UserSettings {
  // 搜索设置
  searchSources: {
    web: boolean
    documents: boolean
    knowledge: boolean
    isEnabled: boolean
    maxResults: number
    timeout: number
  }
  
  // 搜索行为设置
  searchBehavior: {
    enableSuggestions: boolean
    saveHistory: boolean
    autoComplete: boolean
    defaultMode: 'simple' | 'advanced' | 'semantic'
  }
  
  // 高级设置
  advanced: {
    cacheEnabled: boolean
    cacheSize: number
    retryAttempts: number
    debugMode: boolean
    enableExperimentalFeatures: boolean
    apiTimeout: number
  }
  
  // 界面设置
  ui: {
    theme: 'light' | 'dark' | 'system'
    language: string
    fontSize: 'small' | 'medium' | 'large'
    compactMode: boolean
    showPreview: boolean
    animationsEnabled: boolean
  }
  
  // 通知设置
  notifications: {
    enabled: boolean
    email: boolean
    push: boolean
    sound: boolean
    searchComplete: boolean
    documentProcessed: boolean
    systemUpdates: boolean
  }
  
  // 隐私设置
  privacy: {
    shareUsageData: boolean
    allowAnalytics: boolean
    saveSearchHistory: boolean
    autoDeleteHistory: boolean
    historyRetentionDays: number
  }
}

/**
 * 系统配置
 */
export interface SystemConfig {
  version: string
  features: {
    voiceSearch: boolean
    documentUpload: boolean
    advancedSearch: boolean
    exportData: boolean
    apiAccess: boolean
  }
  limits: {
    maxFileSize: number
    maxFilesPerUpload: number
    maxSearchResults: number
    maxHistoryItems: number
    apiRateLimit: number
  }
  supportedFormats: string[]
  defaultSettings: Partial<UserSettings>
}

/**
 * 设置更新请求
 */
export interface SettingsUpdateRequest {
  settings: Partial<UserSettings>
  merge?: boolean // 是否合并更新，默认为 true
}

/**
 * 设置导入/导出格式
 */
export interface SettingsExport {
  version: string
  timestamp: string
  settings: UserSettings
  metadata?: Record<string, any>
}

/**
 * 设置 API 类
 */
class SettingsApi {
  /**
   * 获取用户设置
   */
  async getUserSettings(): Promise<ApiResponse<UserSettings>> {
    try {
      return await apiClient.get<UserSettings>('/settings')
    } catch (error) {
      console.error('获取用户设置失败:', error)
      throw error
    }
  }

  /**
   * 更新用户设置
   */
  async updateUserSettings(
    settings: Partial<UserSettings>,
    merge: boolean = true
  ): Promise<ApiResponse<UserSettings>> {
    try {
      return await apiClient.put<UserSettings>('/settings', {
        settings,
        merge
      })
    } catch (error) {
      console.error('更新用户设置失败:', error)
      throw error
    }
  }

  /**
   * 重置用户设置
   */
  async resetUserSettings(): Promise<ApiResponse<UserSettings>> {
    try {
      return await apiClient.post<UserSettings>('/settings/reset')
    } catch (error) {
      console.error('重置用户设置失败:', error)
      throw error
    }
  }

  /**
   * 获取系统配置
   */
  async getSystemConfig(): Promise<ApiResponse<SystemConfig>> {
    try {
      return await apiClient.get<SystemConfig>('/settings/system')
    } catch (error) {
      console.error('获取系统配置失败:', error)
      throw error
    }
  }

  /**
   * 获取默认设置
   */
  async getDefaultSettings(): Promise<ApiResponse<UserSettings>> {
    try {
      return await apiClient.get<UserSettings>('/settings/defaults')
    } catch (error) {
      console.error('获取默认设置失败:', error)
      throw error
    }
  }

  /**
   * 导出用户设置
   */
  async exportSettings(): Promise<Blob> {
    try {
      return await apiClient.download('/settings/export')
    } catch (error) {
      console.error('导出设置失败:', error)
      throw error
    }
  }

  /**
   * 导入用户设置
   */
  async importSettings(
    file: File,
    merge: boolean = true
  ): Promise<ApiResponse<UserSettings>> {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('merge', merge.toString())
      
      return await apiClient.upload<UserSettings>('/settings/import', formData)
    } catch (error) {
      console.error('导入设置失败:', error)
      throw error
    }
  }

  /**
   * 验证设置数据
   */
  async validateSettings(settings: Partial<UserSettings>): Promise<ApiResponse<{
    valid: boolean
    errors?: Array<{
      field: string
      message: string
    }>
  }>> {
    try {
      return await apiClient.post('/settings/validate', { settings })
    } catch (error) {
      console.error('验证设置失败:', error)
      throw error
    }
  }

  /**
   * 获取设置历史
   */
  async getSettingsHistory(params?: {
    page?: number
    limit?: number
  }): Promise<ApiResponse<{
    items: Array<{
      id: string
      timestamp: string
      changes: Record<string, any>
      version: string
    }>
    total: number
    page: number
    limit: number
  }>> {
    try {
      return await apiClient.get('/settings/history', { params })
    } catch (error) {
      console.error('获取设置历史失败:', error)
      throw error
    }
  }

  /**
   * 恢复到历史版本
   */
  async restoreSettings(historyId: string): Promise<ApiResponse<UserSettings>> {
    try {
      return await apiClient.post<UserSettings>(`/settings/restore/${historyId}`)
    } catch (error) {
      console.error('恢复设置失败:', error)
      throw error
    }
  }

  /**
   * 获取设置模板
   */
  async getSettingsTemplates(): Promise<ApiResponse<Array<{
    id: string
    name: string
    description: string
    settings: Partial<UserSettings>
    category: string
  }>>> {
    try {
      return await apiClient.get('/settings/templates')
    } catch (error) {
      console.error('获取设置模板失败:', error)
      throw error
    }
  }

  /**
   * 应用设置模板
   */
  async applySettingsTemplate(
    templateId: string,
    merge: boolean = true
  ): Promise<ApiResponse<UserSettings>> {
    try {
      return await apiClient.post<UserSettings>(`/settings/templates/${templateId}/apply`, {
        merge
      })
    } catch (error) {
      console.error('应用设置模板失败:', error)
      throw error
    }
  }

  /**
   * 同步设置到云端
   */
  async syncSettings(): Promise<ApiResponse<{
    synced: boolean
    timestamp: string
    conflicts?: Array<{
      field: string
      local: any
      remote: any
    }>
  }>> {
    try {
      return await apiClient.post('/settings/sync')
    } catch (error) {
      console.error('同步设置失败:', error)
      throw error
    }
  }

  /**
   * 解决设置冲突
   */
  async resolveSettingsConflicts(resolutions: Array<{
    field: string
    value: any
    source: 'local' | 'remote'
  }>): Promise<ApiResponse<UserSettings>> {
    try {
      return await apiClient.post<UserSettings>('/settings/resolve-conflicts', {
        resolutions
      })
    } catch (error) {
      console.error('解决设置冲突失败:', error)
      throw error
    }
  }
}

// 创建设置 API 实例
const settingsApi = new SettingsApi()

// 导出实例
export { settingsApi }
export default settingsApi

// 导出类型
export { SettingsApi }