import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { settingsApi } from '@/api'
import type { UserSettings } from '@/api/settings'

/**
 * 主题类型
 */
export type Theme = 'light' | 'dark' | 'auto'

/**
 * 语言类型
 */
export type Language = 'zh-CN' | 'en-US' | 'auto'

/**
 * 搜索源配置
 */
export interface SearchSource {
  id: string
  name: string
  enabled: boolean
  icon: string
  description: string
  priority: number
  config?: Record<string, any>
}

/**
 * 搜索行为设置
 */
export interface SearchBehavior {
  maxResults: number
  timeout: number
  autoScroll: boolean
  showProcessSteps: boolean
  enableSuggestions: boolean
  saveHistory: boolean
  maxHistoryItems: number
}

/**
 * 界面设置
 */
export interface InterfaceSettings {
  theme: Theme
  language: Language
  fontSize: 'small' | 'medium' | 'large'
  compactMode: boolean
  showSidebar: boolean
  sidebarCollapsed: boolean
  animationsEnabled: boolean
}

/**
 * 高级设置
 */
export interface AdvancedSettings {
  debugMode: boolean
  enableExperimentalFeatures: boolean
  cacheEnabled: boolean
  cacheSize: number
  logLevel: 'error' | 'warn' | 'info' | 'debug'
  apiTimeout: number
  retryAttempts: number
  enableAnalytics: boolean
}

/**
 * 通知设置
 */
export interface NotificationSettings {
  enabled: boolean
  searchComplete: boolean
  uploadComplete: boolean
  errors: boolean
  position: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left'
  duration: number
}

/**
 * 快捷键设置
 */
export interface KeyboardShortcuts {
  search: string
  newSearch: string
  clearSearch: string
  toggleSidebar: string
  toggleTheme: string
  focusSearch: string
}

/**
 * 导出设置
 */
export interface ExportSettings {
  defaultFormat: 'json' | 'csv' | 'pdf' | 'markdown'
  includeMetadata: boolean
  includeHighlights: boolean
  maxExportItems: number
}

/**
 * 设置状态接口
 */
interface SettingsState {
  // 设置数据
  searchSources: SearchSource[]
  searchBehavior: SearchBehavior
  interface: InterfaceSettings
  advanced: AdvancedSettings
  notifications: NotificationSettings
  shortcuts: KeyboardShortcuts
  export: ExportSettings
  
  // UI状态
  loading: boolean
  error: string | null
  hasUnsavedChanges: boolean
  
  // Actions
  updateSearchSources: (sources: SearchSource[]) => void
  toggleSearchSource: (sourceId: string) => void
  updateSearchBehavior: (behavior: Partial<SearchBehavior>) => void
  updateInterface: (settings: Partial<InterfaceSettings>) => void
  updateAdvanced: (settings: Partial<AdvancedSettings>) => void
  updateNotifications: (settings: Partial<NotificationSettings>) => void
  updateShortcuts: (shortcuts: Partial<KeyboardShortcuts>) => void
  updateExport: (settings: Partial<ExportSettings>) => void
  
  // 主题相关
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
  
  // 数据操作
  saveSettings: () => Promise<void>
  loadSettings: () => Promise<void>
  resetSettings: () => void
  exportSettings: () => string
  importSettings: (settingsJson: string) => boolean
  
  // 验证
  validateSettings: () => boolean
  
  // 内部方法
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setUnsavedChanges: (hasChanges: boolean) => void
}

/**
 * 默认搜索源配置
 */
const DEFAULT_SEARCH_SOURCES: SearchSource[] = [
  {
    id: 'google',
    name: 'Google',
    enabled: true,
    icon: 'fab fa-google',
    description: '全球最大的搜索引擎',
    priority: 1
  },
  {
    id: 'bing',
    name: 'Bing',
    enabled: true,
    icon: 'fab fa-microsoft',
    description: '微软搜索引擎',
    priority: 2
  },
  {
    id: 'baidu',
    name: '百度',
    enabled: true,
    icon: 'fas fa-search',
    description: '中文搜索引擎',
    priority: 3
  },
  {
    id: 'duckduckgo',
    name: 'DuckDuckGo',
    enabled: false,
    icon: 'fas fa-globe',
    description: '隐私保护搜索',
    priority: 4
  }
]

/**
 * 默认搜索行为设置
 */
const DEFAULT_SEARCH_BEHAVIOR: SearchBehavior = {
  maxResults: 10,
  timeout: 120,
  autoScroll: true,
  showProcessSteps: true,
  enableSuggestions: true,
  saveHistory: true,
  maxHistoryItems: 50
}

/**
 * 默认界面设置
 */
const DEFAULT_INTERFACE: InterfaceSettings = {
  theme: 'auto',
  language: 'zh-CN',
  fontSize: 'medium',
  compactMode: false,
  showSidebar: true,
  sidebarCollapsed: false,
  animationsEnabled: true
}

/**
 * 默认高级设置
 */
const DEFAULT_ADVANCED: AdvancedSettings = {
  debugMode: false,
  enableExperimentalFeatures: false,
  cacheEnabled: true,
  cacheSize: 100,
  logLevel: 'warn',
  apiTimeout: 30000,
  retryAttempts: 3,
  enableAnalytics: true
}

/**
 * 默认通知设置
 */
const DEFAULT_NOTIFICATIONS: NotificationSettings = {
  enabled: true,
  searchComplete: true,
  uploadComplete: true,
  errors: true,
  position: 'top-right',
  duration: 5000
}

/**
 * 默认快捷键设置
 */
const DEFAULT_SHORTCUTS: KeyboardShortcuts = {
  search: 'Enter',
  newSearch: 'Ctrl+N',
  clearSearch: 'Ctrl+K',
  toggleSidebar: 'Ctrl+B',
  toggleTheme: 'Ctrl+Shift+T',
  focusSearch: 'Ctrl+F'
}

/**
 * 默认导出设置
 */
const DEFAULT_EXPORT: ExportSettings = {
  defaultFormat: 'json',
  includeMetadata: true,
  includeHighlights: true,
  maxExportItems: 1000
}

/**
 * 获取系统主题
 */
const getSystemTheme = (): 'light' | 'dark' => {
  if (typeof window !== 'undefined') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return 'light'
}

/**
 * 应用主题到DOM
 */
const applyTheme = (theme: Theme) => {
  if (typeof window === 'undefined') return
  
  const actualTheme = theme === 'auto' ? getSystemTheme() : theme
  const root = window.document.documentElement
  
  root.classList.remove('light', 'dark')
  root.classList.add(actualTheme)
  
  // 更新meta标签
  const metaTheme = document.querySelector('meta[name="theme-color"]')
  if (metaTheme) {
    metaTheme.setAttribute('content', actualTheme === 'dark' ? '#1a1a1a' : '#ffffff')
  }
}

/**
 * 创建设置状态管理store
 */
export const useSettingsStore = create<SettingsState>()(persist(
  (set, get) => ({
    // 初始状态
    searchSources: DEFAULT_SEARCH_SOURCES,
    searchBehavior: DEFAULT_SEARCH_BEHAVIOR,
    interface: DEFAULT_INTERFACE,
    advanced: DEFAULT_ADVANCED,
    notifications: DEFAULT_NOTIFICATIONS,
    shortcuts: DEFAULT_SHORTCUTS,
    export: DEFAULT_EXPORT,
    
    loading: false,
    error: null,
    hasUnsavedChanges: false,
    
    // Actions
    updateSearchSources: (sources) => {
      set({ searchSources: sources, hasUnsavedChanges: true })
    },
    
    toggleSearchSource: (sourceId) => {
      const { searchSources } = get()
      const updatedSources = searchSources.map(source => 
        source.id === sourceId ? { ...source, enabled: !source.enabled } : source
      )
      set({ searchSources: updatedSources, hasUnsavedChanges: true })
    },
    
    updateSearchBehavior: (behavior) => {
      const current = get().searchBehavior
      set({ 
        searchBehavior: { ...current, ...behavior }, 
        hasUnsavedChanges: true 
      })
    },
    
    updateInterface: (settings) => {
      const current = get().interface
      const updated = { ...current, ...settings }
      
      // 如果主题发生变化，立即应用
      if (settings.theme && settings.theme !== current.theme) {
        applyTheme(settings.theme)
      }
      
      set({ 
        interface: updated, 
        hasUnsavedChanges: true 
      })
    },
    
    updateAdvanced: (settings) => {
      const current = get().advanced
      set({ 
        advanced: { ...current, ...settings }, 
        hasUnsavedChanges: true 
      })
    },
    
    updateNotifications: (settings) => {
      const current = get().notifications
      set({ 
        notifications: { ...current, ...settings }, 
        hasUnsavedChanges: true 
      })
    },
    
    updateShortcuts: (shortcuts) => {
      const current = get().shortcuts
      set({ 
        shortcuts: { ...current, ...shortcuts }, 
        hasUnsavedChanges: true 
      })
    },
    
    updateExport: (settings) => {
      const current = get().export
      set({ 
        export: { ...current, ...settings }, 
        hasUnsavedChanges: true 
      })
    },
    
    setTheme: (theme) => {
      get().updateInterface({ theme })
    },
    
    toggleTheme: () => {
      const { interface: currentInterface } = get()
      const currentTheme = currentInterface.theme
      
      let newTheme: Theme
      if (currentTheme === 'light') {
        newTheme = 'dark'
      } else if (currentTheme === 'dark') {
        newTheme = 'auto'
      } else {
        newTheme = 'light'
      }
      
      get().setTheme(newTheme)
    },
    
    saveSettings: async () => {
      set({ loading: true, error: null })
      
      try {
        // 验证设置
        if (!get().validateSettings()) {
          return
        }
        
        const {
          searchSources,
          searchBehavior,
          interface: interfaceSettings,
          advanced,
          notifications
        } = get()
        
        // 构建API格式的设置数据
        const userSettings: Partial<UserSettings> = {
          searchSources: {
            web: searchSources.find(s => s.id === 'google')?.enabled || false,
            documents: true,
            knowledge: true,
            isEnabled: searchSources.some(s => s.enabled),
            maxResults: searchBehavior.maxResults,
            timeout: searchBehavior.timeout
          },
          searchBehavior: {
            enableSuggestions: searchBehavior.enableSuggestions,
            saveHistory: searchBehavior.saveHistory,
            autoComplete: true,
            defaultMode: 'simple'
          },
          advanced: {
            cacheEnabled: advanced.cacheEnabled,
            cacheSize: advanced.cacheSize,
            retryAttempts: advanced.retryAttempts,
            debugMode: advanced.debugMode,
            enableExperimentalFeatures: advanced.enableExperimentalFeatures,
            apiTimeout: advanced.apiTimeout
          },
          ui: {
            theme: interfaceSettings.theme === 'auto' ? 'system' : interfaceSettings.theme,
            language: interfaceSettings.language as string,
            fontSize: interfaceSettings.fontSize,
            compactMode: interfaceSettings.compactMode,
            showPreview: true,
            animationsEnabled: interfaceSettings.animationsEnabled
          },
          notifications: {
            enabled: notifications.enabled,
            email: false,
            push: false,
            sound: false,
            searchComplete: notifications.searchComplete,
            documentProcessed: notifications.uploadComplete,
            systemUpdates: false
          }
        }
        
        const response = await settingsApi.updateUserSettings(userSettings)
        
        if (!response.success) {
          throw new Error(response.error || '保存设置失败')
        }
        
        set({ hasUnsavedChanges: false })
        
      } catch (error: any) {
        const errorMessage = error?.error || error?.message || '保存设置失败，请稍后重试'
        set({ error: errorMessage })
        console.error('保存设置错误:', error)
      } finally {
        set({ loading: false })
      }
    },
    
    loadSettings: async () => {
      set({ loading: true, error: null })
      
      try {
        const response = await settingsApi.getUserSettings()
        
        if (!response.success || !response.data) {
          // 如果获取失败，使用默认设置
          console.warn('获取用户设置失败，使用默认设置')
          return
        }
        
        const userSettings = response.data
        
        // 转换API数据为store格式
        const updatedSearchSources = DEFAULT_SEARCH_SOURCES.map(source => {
          if (source.id === 'google') {
            return { ...source, enabled: userSettings.searchSources?.web || false }
          }
          return source
        })
        
        const updatedSearchBehavior: SearchBehavior = {
          ...DEFAULT_SEARCH_BEHAVIOR,
          maxResults: userSettings.searchSources?.maxResults || DEFAULT_SEARCH_BEHAVIOR.maxResults,
          timeout: userSettings.searchSources?.timeout || DEFAULT_SEARCH_BEHAVIOR.timeout,
          enableSuggestions: userSettings.searchBehavior?.enableSuggestions ?? DEFAULT_SEARCH_BEHAVIOR.enableSuggestions,
          saveHistory: userSettings.searchBehavior?.saveHistory ?? DEFAULT_SEARCH_BEHAVIOR.saveHistory
        }
        
        const updatedInterface: InterfaceSettings = {
          ...DEFAULT_INTERFACE,
          theme: (userSettings.ui?.theme === 'system' ? 'auto' : userSettings.ui?.theme) || DEFAULT_INTERFACE.theme,
          language: (userSettings.ui?.language as Language) || DEFAULT_INTERFACE.language,
          fontSize: userSettings.ui?.fontSize || DEFAULT_INTERFACE.fontSize,
          compactMode: userSettings.ui?.compactMode ?? DEFAULT_INTERFACE.compactMode,
          animationsEnabled: userSettings.ui?.animationsEnabled ?? DEFAULT_INTERFACE.animationsEnabled
        }
        
        const updatedAdvanced: AdvancedSettings = {
          ...DEFAULT_ADVANCED,
          cacheEnabled: userSettings.advanced?.cacheEnabled ?? DEFAULT_ADVANCED.cacheEnabled,
          cacheSize: userSettings.advanced?.cacheSize || DEFAULT_ADVANCED.cacheSize,
          retryAttempts: userSettings.advanced?.retryAttempts || DEFAULT_ADVANCED.retryAttempts,
          debugMode: userSettings.advanced?.debugMode ?? DEFAULT_ADVANCED.debugMode,
          enableExperimentalFeatures: userSettings.advanced?.enableExperimentalFeatures ?? DEFAULT_ADVANCED.enableExperimentalFeatures,
          apiTimeout: userSettings.advanced?.apiTimeout || DEFAULT_ADVANCED.apiTimeout
        }
        
        const updatedNotifications: NotificationSettings = {
          ...DEFAULT_NOTIFICATIONS,
          enabled: userSettings.notifications?.enabled ?? DEFAULT_NOTIFICATIONS.enabled,
          searchComplete: userSettings.notifications?.searchComplete ?? DEFAULT_NOTIFICATIONS.searchComplete,
          uploadComplete: userSettings.notifications?.documentProcessed ?? DEFAULT_NOTIFICATIONS.uploadComplete
        }
        
        // 更新store状态
        set({
          searchSources: updatedSearchSources,
          searchBehavior: updatedSearchBehavior,
          interface: updatedInterface,
          advanced: updatedAdvanced,
          notifications: updatedNotifications,
          hasUnsavedChanges: false
        })
        
        // 应用主题
        applyTheme(updatedInterface.theme)
        
      } catch (error: any) {
        const errorMessage = error?.error || error?.message || '加载设置失败，请稍后重试'
        set({ error: errorMessage })
        console.error('加载设置错误:', error)
      } finally {
        set({ loading: false })
      }
    },
    
    resetSettings: () => {
      set({
        searchSources: DEFAULT_SEARCH_SOURCES,
        searchBehavior: DEFAULT_SEARCH_BEHAVIOR,
        interface: DEFAULT_INTERFACE,
        advanced: DEFAULT_ADVANCED,
        notifications: DEFAULT_NOTIFICATIONS,
        shortcuts: DEFAULT_SHORTCUTS,
        export: DEFAULT_EXPORT,
        hasUnsavedChanges: true
      })
      
      // 重新应用主题
      applyTheme(DEFAULT_INTERFACE.theme)
    },
    
    exportSettings: () => {
      const {
        searchSources,
        searchBehavior,
        interface: interfaceSettings,
        advanced,
        notifications,
        shortcuts,
        export: exportSettings
      } = get()
      
      const settings = {
        searchSources,
        searchBehavior,
        interface: interfaceSettings,
        advanced,
        notifications,
        shortcuts,
        export: exportSettings,
        exportTime: new Date().toISOString(),
        version: '1.0.0'
      }
      
      return JSON.stringify(settings, null, 2)
    },
    
    importSettings: (settingsJson) => {
      try {
        const settings = JSON.parse(settingsJson)
        
        // 验证设置格式
        if (!settings || typeof settings !== 'object') {
          throw new Error('无效的设置格式')
        }
        
        // 导入设置
        if (settings.searchSources) {
          set({ searchSources: settings.searchSources })
        }
        if (settings.searchBehavior) {
          set({ searchBehavior: settings.searchBehavior })
        }
        if (settings.interface) {
          set({ interface: settings.interface })
          applyTheme(settings.interface.theme)
        }
        if (settings.advanced) {
          set({ advanced: settings.advanced })
        }
        if (settings.notifications) {
          set({ notifications: settings.notifications })
        }
        if (settings.shortcuts) {
          set({ shortcuts: settings.shortcuts })
        }
        if (settings.export) {
          set({ export: settings.export })
        }
        
        set({ hasUnsavedChanges: true })
        return true
        
      } catch (error) {
        set({ error: '导入设置失败，请检查文件格式' })
        console.error('导入设置错误:', error)
        return false
      }
    },
    
    validateSettings: () => {
      const {
        searchBehavior,
        advanced,
        notifications
      } = get()
      
      // 验证搜索行为设置
      if (searchBehavior.maxResults < 1 || searchBehavior.maxResults > 100) {
        set({ error: '最大搜索结果数必须在1-100之间' })
        return false
      }
      
      if (searchBehavior.timeout < 10 || searchBehavior.timeout > 600) {
        set({ error: '搜索超时时间必须在10-600秒之间' })
        return false
      }
      
      // 验证高级设置
      if (advanced.cacheSize < 10 || advanced.cacheSize > 1000) {
        set({ error: '缓存大小必须在10-1000之间' })
        return false
      }
      
      if (advanced.apiTimeout < 5000 || advanced.apiTimeout > 120000) {
        set({ error: 'API超时时间必须在5-120秒之间' })
        return false
      }
      
      // 验证通知设置
      if (notifications.duration < 1000 || notifications.duration > 30000) {
        set({ error: '通知持续时间必须在1-30秒之间' })
        return false
      }
      
      return true
    },
    
    setLoading: (loading) => set({ loading }),
    setError: (error) => set({ error }),
    setUnsavedChanges: (hasUnsavedChanges) => set({ hasUnsavedChanges })
  }),
  {
    name: 'settings-store',
    partialize: (state) => ({
      searchSources: state.searchSources,
      searchBehavior: state.searchBehavior,
      interface: state.interface,
      advanced: state.advanced,
      notifications: state.notifications,
      shortcuts: state.shortcuts,
      export: state.export
    }),
    onRehydrateStorage: () => (state) => {
      // 在状态恢复后应用主题
      if (state?.interface?.theme) {
        applyTheme(state.interface.theme)
      }
    }
  }
))

/**
 * 设置store的hook
 */
export const useSettings = () => {
  const store = useSettingsStore()
  return {
    ...store,
    // 便捷方法
    enabledSearchSources: store.searchSources.filter(source => source.enabled),
    currentTheme: store.interface.theme === 'auto' ? getSystemTheme() : store.interface.theme,
    isDarkMode: (store.interface.theme === 'auto' ? getSystemTheme() : store.interface.theme) === 'dark'
  }
}

/**
 * 初始化设置
 */
export const initializeSettings = () => {
  const store = useSettingsStore.getState()
  
  // 应用主题
  applyTheme(store.interface.theme)
  
  // 监听系统主题变化
  if (typeof window !== 'undefined' && store.interface.theme === 'auto') {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = () => {
      if (store.interface.theme === 'auto') {
        applyTheme('auto')
      }
    }
    
    mediaQuery.addEventListener('change', handleChange)
    
    // 返回清理函数
    return () => mediaQuery.removeEventListener('change', handleChange)
  }
}