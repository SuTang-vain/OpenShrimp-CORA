import { apiClient } from './client'
import type { ApiResponse } from '@/types'

/**
 * 搜索请求参数
 */
export interface SearchRequest {
  query: string
  sources?: string[]
  mode?: 'simple' | 'advanced' | 'semantic'
  maxResults?: number
  timeout?: number
  enableSuggestions?: boolean
  saveHistory?: boolean
}

/**
 * 搜索结果项
 */
export interface SearchResultItem {
  id: string
  title: string
  content: string
  url?: string
  source: string
  score: number
  timestamp: string
  metadata?: Record<string, any>
}

/**
 * 搜索响应数据
 */
export interface SearchResponse {
  results: SearchResultItem[]
  total: number
  query: string
  duration: number
  suggestions?: string[]
  searchId: string
}

/**
 * 搜索历史项
 */
export interface SearchHistoryItem {
  id: string
  query: string
  timestamp: string
  resultCount: number
  duration: number
  sources: string[]
  mode: string
}

/**
 * 搜索建议响应
 */
export interface SearchSuggestionsResponse {
  suggestions: string[]
  query: string
}

/**
 * 搜索 API 类
 */
class SearchApi {
  /**
   * 执行搜索
   */
  async search(params: SearchRequest): Promise<ApiResponse<SearchResponse>> {
    try {
      // 映射为后端期望的字段
      const payload: any = {
        query: params.query,
        strategy:
          params.mode === 'semantic'
            ? 'similarity'
            : params.mode === 'advanced'
            ? 'hybrid'
            : 'keyword',
        top_k: params.maxResults ?? 20,
        include_metadata: true,
        expand_query: params.enableSuggestions ?? false,
        filters:
          params.sources && params.sources.length
            ? { source: params.sources[0] }
            : undefined,
      }

      const res = await apiClient.post<any>('/query', payload)

      // 如果失败或没有数据，直接返回
      if (!res.success || !res.data) {
        return res as ApiResponse<any>
      }

      // 将后端响应转换为前端 SearchResponse 结构
      const d = res.data as any
      const transformed: SearchResponse = {
        results: (d.results || []).map((it: any, idx: number) => ({
          id: it?.chunk_id || `${it?.doc_id || 'unknown'}:${it?.chunk_id || idx}`,
          title: it?.title,
          content: it?.content,
          url: it?.url,
          source: it?.source,
          score: it?.score,
          timestamp: '',
          metadata: it?.metadata,
        })),
        total: d?.total_results ?? (Array.isArray(d?.results) ? d.results.length : 0),
        query: d?.query,
        duration: d?.execution_time ?? 0,
        suggestions: d?.metadata?.suggestions || undefined,
        searchId: d?.metadata?.search_id || '',
      }

      return { ...res, data: transformed }
    } catch (error) {
      console.error('搜索失败:', error)
      throw error
    }
  }

  /**
   * 获取搜索建议
   */
  async getSuggestions(query: string): Promise<ApiResponse<SearchSuggestionsResponse>> {
    try {
      return await apiClient.get<SearchSuggestionsResponse>('/suggestions', {
        params: { query }
      })
    } catch (error) {
      console.error('获取搜索建议失败:', error)
      throw error
    }
  }

  /**
   * 获取搜索历史
   */
  async getSearchHistory(params?: {
    page?: number
    limit?: number
    startDate?: string
    endDate?: string
  }): Promise<ApiResponse<{
    items: SearchHistoryItem[]
    total: number
    page: number
    limit: number
  }>> {
    try {
      return await apiClient.get('/search/history', { params })
    } catch (error) {
      console.error('获取搜索历史失败:', error)
      throw error
    }
  }

  /**
   * 删除搜索历史项
   */
  async deleteSearchHistory(id: string): Promise<ApiResponse<void>> {
    try {
      return await apiClient.delete(`/search/history/${id}`)
    } catch (error) {
      console.error('删除搜索历史失败:', error)
      throw error
    }
  }

  /**
   * 清空搜索历史
   */
  async clearSearchHistory(): Promise<ApiResponse<void>> {
    try {
      return await apiClient.delete('/search/history')
    } catch (error) {
      console.error('清空搜索历史失败:', error)
      throw error
    }
  }

  /**
   * 获取搜索统计信息
   */
  async getSearchStats(params?: {
    startDate?: string
    endDate?: string
  }): Promise<ApiResponse<{
    totalSearches: number
    avgDuration: number
    topQueries: Array<{ query: string; count: number }>
    topSources: Array<{ source: string; count: number }>
  }>> {
    try {
      return await apiClient.get('/search/stats', { params })
    } catch (error) {
      console.error('获取搜索统计失败:', error)
      throw error
    }
  }

  /**
   * 获取搜索详情
   */
  async getSearchDetails(searchId: string): Promise<ApiResponse<SearchResponse>> {
    try {
      return await apiClient.get<SearchResponse>(`/search/${searchId}`)
    } catch (error) {
      console.error('获取搜索详情失败:', error)
      throw error
    }
  }

  /**
   * 导出搜索历史
   */
  async exportSearchHistory(format: 'json' | 'csv' | 'xlsx' = 'json'): Promise<Blob> {
    try {
      return await apiClient.download('/search/history/export', {
        params: { format }
      })
    } catch (error) {
      console.error('导出搜索历史失败:', error)
      throw error
    }
  }
}

// 创建搜索 API 实例
const searchApi = new SearchApi()

// 导出实例
export { searchApi }
export default searchApi

// 导出类型
export { SearchApi }