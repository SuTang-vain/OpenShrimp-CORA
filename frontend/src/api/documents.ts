import { apiClient } from './client'
import type { ApiResponse } from '@/types'
import type { DocumentInfo, DocumentStatus, DocumentType } from '@/stores/documentStore'

/**
 * 文档上传请求参数
 */
export interface DocumentUploadRequest {
  files: File[]
  metadata?: Record<string, any>
  tags?: string[]
  category?: string
}

/**
 * 文档上传响应
 */
export interface DocumentUploadResponse {
  documents: DocumentInfo[]
  failed: Array<{
    filename: string
    error: string
  }>
}

/**
 * 文档查询参数
 */
export interface DocumentQueryParams {
  page?: number
  limit?: number
  search?: string
  type?: DocumentType
  status?: DocumentStatus
  tags?: string[]
  startDate?: string
  endDate?: string
  sortBy?: 'name' | 'date' | 'size' | 'type'
  sortOrder?: 'asc' | 'desc'
}

/**
 * 文档列表响应
 */
export interface DocumentListResponse {
  documents: DocumentInfo[]
  total: number
  page: number
  limit: number
  totalPages: number
}

/**
 * 文档统计信息
 */
export interface DocumentStats {
  total: number
  byType: Record<DocumentType, number>
  byStatus: Record<DocumentStatus, number>
  totalSize: number
  avgSize: number
  recentUploads: number
}

/**
 * 文档处理状态
 */
export interface DocumentProcessingStatus {
  id: string
  status: DocumentStatus
  progress: number
  message?: string
  error?: string
}

/**
 * 文档 API 类
 */
class DocumentsApi {
  /**
   * 上传文档
   */
  async uploadDocuments(
    files: File[],
    metadata?: Record<string, any>,
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<DocumentUploadResponse>> {
    try {
      const formData = new FormData()
      
      // 添加文件
      files.forEach((file) => {
        formData.append(`files`, file)
      })
      
      // 添加元数据
      if (metadata) {
        formData.append('metadata', JSON.stringify(metadata))
      }
      
      return await apiClient.upload<DocumentUploadResponse>('/documents/upload', formData, {
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(progress)
          }
        }
      })
    } catch (error) {
      console.error('文档上传失败:', error)
      throw error
    }
  }

  /**
   * 获取文档列表
   */
  async getDocuments(params?: DocumentQueryParams): Promise<ApiResponse<DocumentListResponse>> {
    try {
      return await apiClient.get<DocumentListResponse>('/documents', { params })
    } catch (error) {
      console.error('获取文档列表失败:', error)
      throw error
    }
  }

  /**
   * 获取文档详情
   */
  async getDocument(id: string): Promise<ApiResponse<DocumentInfo>> {
    try {
      return await apiClient.get<DocumentInfo>(`/documents/${id}`)
    } catch (error) {
      console.error('获取文档详情失败:', error)
      throw error
    }
  }

  /**
   * 更新文档信息
   */
  async updateDocument(
    id: string,
    updates: Partial<Pick<DocumentInfo, 'name' | 'metadata'>>
  ): Promise<ApiResponse<DocumentInfo>> {
    try {
      return await apiClient.patch<DocumentInfo>(`/documents/${id}`, updates)
    } catch (error) {
      console.error('更新文档失败:', error)
      throw error
    }
  }

  /**
   * 删除文档
   */
  async deleteDocument(id: string): Promise<ApiResponse<void>> {
    try {
      return await apiClient.delete(`/documents/${id}`)
    } catch (error) {
      console.error('删除文档失败:', error)
      throw error
    }
  }

  /**
   * 批量删除文档
   */
  async batchDeleteDocuments(ids: string[]): Promise<ApiResponse<{
    deleted: string[]
    failed: Array<{ id: string; error: string }>
  }>> {
    try {
      return await apiClient.post('/documents/batch-delete', { ids })
    } catch (error) {
      console.error('批量删除文档失败:', error)
      throw error
    }
  }

  /**
   * 重新处理文档
   */
  async reprocessDocument(id: string): Promise<ApiResponse<void>> {
    try {
      return await apiClient.post(`/documents/${id}/reprocess`)
    } catch (error) {
      console.error('重新处理文档失败:', error)
      throw error
    }
  }

  /**
   * 获取文档处理状态
   */
  async getProcessingStatus(id: string): Promise<ApiResponse<DocumentProcessingStatus>> {
    try {
      return await apiClient.get<DocumentProcessingStatus>(`/documents/${id}/status`)
    } catch (error) {
      console.error('获取文档处理状态失败:', error)
      throw error
    }
  }

  /**
   * 下载文档
   */
  async downloadDocument(id: string): Promise<Blob> {
    try {
      return await apiClient.download(`/documents/${id}/download`)
    } catch (error) {
      console.error('下载文档失败:', error)
      throw error
    }
  }

  /**
   * 获取文档预览
   */
  async getDocumentPreview(id: string): Promise<ApiResponse<{
    content: string
    contentType: string
    pages?: number
  }>> {
    try {
      return await apiClient.get(`/documents/${id}/preview`)
    } catch (error) {
      console.error('获取文档预览失败:', error)
      throw error
    }
  }

  /**
   * 获取文档统计信息
   */
  async getDocumentStats(): Promise<ApiResponse<DocumentStats>> {
    try {
      return await apiClient.get<DocumentStats>('/documents/stats')
    } catch (error) {
      console.error('获取文档统计失败:', error)
      throw error
    }
  }

  /**
   * 搜索文档
   */
  async searchDocuments(params: {
    query: string
    filters?: DocumentQueryParams
  }): Promise<ApiResponse<DocumentListResponse>> {
    try {
      return await apiClient.post<DocumentListResponse>('/documents/search', params)
    } catch (error) {
      console.error('搜索文档失败:', error)
      throw error
    }
  }

  /**
   * 获取文档标签
   */
  async getDocumentTags(): Promise<ApiResponse<string[]>> {
    try {
      return await apiClient.get<string[]>('/documents/tags')
    } catch (error) {
      console.error('获取文档标签失败:', error)
      throw error
    }
  }

  /**
   * 导出文档列表
   */
  async exportDocuments(
    format: 'json' | 'csv' | 'xlsx' = 'json',
    filters?: DocumentQueryParams
  ): Promise<Blob> {
    try {
      return await apiClient.download('/documents/export', {
        params: { format, ...filters }
      })
    } catch (error) {
      console.error('导出文档列表失败:', error)
      throw error
    }
  }
}

// 创建文档 API 实例
const documentsApi = new DocumentsApi()

// 导出实例
export { documentsApi }
export default documentsApi

// 导出类型
export { DocumentsApi }