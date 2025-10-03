import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { searchApi } from '@/api'
import type { SearchRequest } from '@/api/search'

/**
 * 搜索策略枚举
 */
export enum SearchStrategy {
  SIMILARITY = 'similarity',
  KEYWORD = 'keyword',
  HYBRID = 'hybrid',
  SEMANTIC = 'semantic'
}

/**
 * RAG检索模式
 */
export enum RagMode {
  FAST = 'fast',        // 快速检索
  DEEP = 'deep',        // 深度检索
  TOPIC = 'topic',      // 主题检索
  SMART = 'smart'       // 智能检索
}

/**
 * AI模型配置
 */
export interface AIModel {
  id: string
  name: string
  provider: string
  isLocal: boolean
  description?: string
}

/**
 * 搜索步骤状态
 */
export interface SearchStep {
  id: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'error'
  message?: string
  progress?: number
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
  source: string
  title?: string
  url?: string
  metadata?: Record<string, any>
  highlight?: string
}

/**
 * 搜索历史项
 */
export interface SearchHistoryItem {
  id: string
  query: string
  timestamp: number
  resultCount: number
  executionTime: number
  strategy: SearchStrategy
  ragMode?: RagMode
  model: string
}

/**
 * 搜索状态接口
 */
interface SearchState {
  // 搜索基本状态
  query: string
  results: SearchResultItem[]
  loading: boolean
  error: string | null
  totalResults: number
  executionTime: number
  
  // 搜索配置
  strategy: SearchStrategy
  ragMode: RagMode
  ragEnabled: boolean
  selectedModel: AIModel
  availableModels: AIModel[]
  
  // 搜索进度
  searchSteps: SearchStep[]
  currentStep: string | null
  
  // 搜索历史
  searchHistory: SearchHistoryItem[]
  
  // 过滤和排序
  filters: {
    dateRange: string
    fileType: string
    source: string
    minScore: number
  }
  sortBy: 'relevance' | 'date' | 'score'
  sortOrder: 'asc' | 'desc'
  
  // Actions
  setQuery: (query: string) => void
  setResults: (results: SearchResultItem[]) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setStrategy: (strategy: SearchStrategy) => void
  setRagMode: (mode: RagMode) => void
  setRagEnabled: (enabled: boolean) => void
  setSelectedModel: (model: AIModel) => void
  setAvailableModels: (models: AIModel[]) => void
  updateSearchStep: (stepId: string, updates: Partial<SearchStep>) => void
  addToHistory: (item: Omit<SearchHistoryItem, 'id' | 'timestamp'>) => void
  clearHistory: () => void
  setFilters: (filters: Partial<SearchState['filters']>) => void
  setSorting: (sortBy: SearchState['sortBy'], sortOrder: SearchState['sortOrder']) => void
  performSearch: (query: string) => Promise<void>
  resetSearch: () => void
}

/**
 * 默认AI模型列表
 */
const DEFAULT_MODELS: AIModel[] = [
  {
    id: 'qwen2.5-72b',
    name: '通义千问2.5-72B',
    provider: 'Alibaba',
    isLocal: false,
    description: '大型语言模型，适合复杂推理任务'
  },
  {
    id: 'qwen2.5-14b',
    name: '通义千问2.5-14B',
    provider: 'Alibaba',
    isLocal: false,
    description: '中型语言模型，平衡性能和速度'
  },
  {
    id: 'qwen2.5-7b',
    name: '通义千问2.5-7B',
    provider: 'Alibaba',
    isLocal: false,
    description: '轻量级模型，快速响应'
  },
  {
    id: 'glm4.5',
    name: 'GLM4.5',
    provider: 'Zhipu',
    isLocal: false,
    description: '智谱AI大模型'
  },
  {
    id: 'qwen2.5-7b-local',
    name: '通义千问2.5-7B(本地)',
    provider: 'Alibaba',
    isLocal: true,
    description: '本地部署版本'
  },
  {
    id: 'qwen2.5-14b-local',
    name: '通义千问2.5-14B(本地)',
    provider: 'Alibaba',
    isLocal: true,
    description: '本地部署版本'
  },
  {
    id: 'qwen3-32b-local',
    name: '通义千问3-32B(本地)',
    provider: 'Alibaba',
    isLocal: true,
    description: '本地部署版本'
  }
]

/**
 * 默认搜索步骤
 */
const DEFAULT_SEARCH_STEPS: SearchStep[] = [
  {
    id: 'analyze',
    name: '分析查询',
    status: 'pending',
    message: '解析用户意图...'
  },
  {
    id: 'retrieve',
    name: '检索文档',
    status: 'pending',
    message: '搜索知识库...'
  },
  {
    id: 'web_search',
    name: '网络搜索',
    status: 'pending',
    message: '获取最新信息...'
  },
  {
    id: 'generate',
    name: 'AI分析',
    status: 'pending',
    message: '生成回答...'
  }
]

/**
 * 创建搜索状态管理store
 */
export const useSearchStore = create<SearchState>()(persist(
  (set, get) => ({
    // 初始状态
    query: '',
    results: [],
    loading: false,
    error: null,
    totalResults: 0,
    executionTime: 0,
    
    // 搜索配置
    strategy: SearchStrategy.SIMILARITY,
    ragMode: RagMode.FAST,
    ragEnabled: true,
    selectedModel: DEFAULT_MODELS[2], // 默认选择7B模型
    availableModels: DEFAULT_MODELS,
    
    // 搜索进度
    searchSteps: DEFAULT_SEARCH_STEPS,
    currentStep: null,
    
    // 搜索历史
    searchHistory: [],
    
    // 过滤和排序
    filters: {
      dateRange: 'all',
      fileType: 'all',
      source: 'all',
      minScore: 0
    },
    sortBy: 'relevance',
    sortOrder: 'desc',
    
    // Actions
    setQuery: (query) => set({ query }),
    
    setResults: (results) => set({ results, totalResults: results.length }),
    
    setLoading: (loading) => set({ loading }),
    
    setError: (error) => set({ error }),
    
    setStrategy: (strategy) => set({ strategy }),
    
    setRagMode: (ragMode) => set({ ragMode }),
    
    setRagEnabled: (ragEnabled) => set({ ragEnabled }),
    
    setSelectedModel: (selectedModel) => set({ selectedModel }),
    
    setAvailableModels: (availableModels) => set({ availableModels }),
    
    updateSearchStep: (stepId, updates) => {
      const { searchSteps } = get()
      const updatedSteps = searchSteps.map(step => 
        step.id === stepId ? { ...step, ...updates } : step
      )
      set({ searchSteps: updatedSteps, currentStep: stepId })
    },
    
    addToHistory: (item) => {
      const { searchHistory } = get()
      const historyItem: SearchHistoryItem = {
        ...item,
        id: Date.now().toString(),
        timestamp: Date.now()
      }
      const updatedHistory = [historyItem, ...searchHistory.slice(0, 49)] // 保留最近50条
      set({ searchHistory: updatedHistory })
    },
    
    clearHistory: () => set({ searchHistory: [] }),
    
    setFilters: (filters) => {
      const currentFilters = get().filters
      set({ filters: { ...currentFilters, ...filters } })
    },
    
    setSorting: (sortBy, sortOrder) => set({ sortBy, sortOrder }),
    
    performSearch: async (query) => {
      const { selectedModel, strategy, ragMode, ragEnabled, filters } = get()
      
      set({ 
        loading: true, 
        error: null, 
        query,
        searchSteps: DEFAULT_SEARCH_STEPS.map(step => ({ ...step, status: 'pending' as const }))
      })
      
      const startTime = Date.now()
      
      try {
        // 更新搜索步骤
        get().updateSearchStep('analyze', { status: 'running', message: '分析查询意图...' })
        
        // 构建搜索请求参数
        const searchRequest: SearchRequest = {
          query,
          mode: strategy === SearchStrategy.SEMANTIC ? 'semantic' : 
                strategy === SearchStrategy.HYBRID ? 'advanced' : 'simple',
          maxResults: 20,
          timeout: 30000,
          enableSuggestions: true,
          saveHistory: true,
          sources: filters.source === 'all' ? undefined : [filters.source]
        }
        
        get().updateSearchStep('analyze', { status: 'completed' })
        get().updateSearchStep('retrieve', { status: 'running', message: '检索相关文档...' })
        
        // 调用搜索API
        const response = await searchApi.search(searchRequest)
        
        if (!response.success || !response.data) {
          throw new Error(response.error || '搜索请求失败')
        }
        
        const searchData = response.data
        
        get().updateSearchStep('retrieve', { status: 'completed' })
        get().updateSearchStep('web_search', { status: 'running', message: '扩展网络搜索...' })
        
        // 模拟网络搜索步骤
        await new Promise(resolve => setTimeout(resolve, 500))
        
        get().updateSearchStep('web_search', { status: 'completed' })
        get().updateSearchStep('generate', { status: 'running', message: '生成搜索结果...' })
        
        // 转换API结果为store格式
        const results: SearchResultItem[] = searchData.results.map((item, index) => ({
          id: item.id,
          content: item.content,
          score: item.score,
          rank: index + 1,
          docId: item.id,
          chunkId: item.id,
          source: item.source,
          title: item.title,
          url: item.url,
          metadata: item.metadata,
          highlight: item.content // 可以根据需要处理高亮
        }))
        
        get().updateSearchStep('generate', { status: 'completed' })
        
        const endTime = Date.now()
        const executionTime = (endTime - startTime) / 1000
        
        set({ 
          results, 
          totalResults: searchData.total,
          executionTime,
          loading: false 
        })
        
        // 添加到历史记录
        get().addToHistory({
          query,
          resultCount: results.length,
          executionTime,
          strategy,
          ragMode: ragEnabled ? ragMode : undefined,
          model: selectedModel.id
        })
        
      } catch (error: any) {
        // 更新失败的搜索步骤
        const currentSteps = get().searchSteps
        const runningStep = currentSteps.find(step => step.status === 'running')
        if (runningStep) {
          get().updateSearchStep(runningStep.id, { 
            status: 'error', 
            message: '搜索失败' 
          })
        }
        
        const errorMessage = error?.error || error?.message || '搜索失败，请稍后重试'
        set({ 
          error: errorMessage, 
          loading: false 
        })
        console.error('搜索错误:', error)
      }
    },
    
    resetSearch: () => {
      set({
        query: '',
        results: [],
        loading: false,
        error: null,
        totalResults: 0,
        executionTime: 0,
        searchSteps: DEFAULT_SEARCH_STEPS,
        currentStep: null
      })
    }
  }),
  {
    name: 'search-store',
    partialize: (state) => ({
      strategy: state.strategy,
      ragMode: state.ragMode,
      ragEnabled: state.ragEnabled,
      selectedModel: state.selectedModel,
      searchHistory: state.searchHistory,
      filters: state.filters,
      sortBy: state.sortBy,
      sortOrder: state.sortOrder
    })
  }
))

/**
 * 搜索store的hook
 */
export const useSearch = () => {
  const store = useSearchStore()
  return {
    ...store,
    // 便捷方法
    isSearching: store.loading,
    hasResults: store.results.length > 0,
    hasError: !!store.error,
    currentStepName: store.searchSteps.find(step => step.id === store.currentStep)?.name
  }
}