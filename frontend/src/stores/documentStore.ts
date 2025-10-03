import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { documentsApi } from '@/api'

/**
 * 文档状态枚举
 */
export enum DocumentStatus {
  UPLOADING = 'uploading',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  ERROR = 'error',
  DELETED = 'deleted'
}

/**
 * 文档类型枚举
 */
export enum DocumentType {
  PDF = 'pdf',
  DOC = 'doc',
  DOCX = 'docx',
  TXT = 'txt',
  MD = 'md',
  HTML = 'html',
  OTHER = 'other'
}

/**
 * 文档信息接口
 */
export interface DocumentInfo {
  id: string
  name: string
  originalName: string
  type: DocumentType
  size: number
  status: DocumentStatus
  uploadTime: number
  processTime?: number
  completedTime?: number
  url?: string
  thumbnailUrl?: string
  metadata: {
    author?: string
    title?: string
    description?: string
    tags: string[]
    pageCount?: number
    wordCount?: number
    language?: string
  }
  processingInfo?: {
    progress: number
    stage: string
    message: string
  }
  error?: string
}

/**
 * 上传进度信息
 */
export interface UploadProgress {
  fileId: string
  fileName: string
  progress: number
  speed: number
  remainingTime: number
  status: 'uploading' | 'completed' | 'error'
  error?: string
}

/**
 * 文档过滤器
 */
export interface DocumentFilters {
  status: DocumentStatus | 'all'
  type: DocumentType | 'all'
  dateRange: string
  searchQuery: string
  tags: string[]
}

/**
 * 批量操作类型
 */
export type BatchOperation = 'delete' | 'reprocess' | 'export' | 'tag'

/**
 * 文档统计信息
 */
export interface DocumentStats {
  total: number
  byStatus: Record<DocumentStatus, number>
  byType: Record<DocumentType, number>
  totalSize: number
  averageProcessingTime: number
}

/**
 * 文档状态接口
 */
interface DocumentState {
  // 文档列表
  documents: DocumentInfo[]
  selectedDocuments: string[]
  
  // 上传状态
  uploadQueue: UploadProgress[]
  isUploading: boolean
  
  // UI状态
  loading: boolean
  error: string | null
  
  // 过滤和排序
  filters: DocumentFilters
  sortBy: 'name' | 'uploadTime' | 'size' | 'status'
  sortOrder: 'asc' | 'desc'
  
  // 分页
  currentPage: number
  pageSize: number
  totalPages: number
  
  // 统计信息
  stats: DocumentStats
  
  // Actions
  setDocuments: (documents: DocumentInfo[]) => void
  addDocument: (document: DocumentInfo) => void
  updateDocument: (id: string, updates: Partial<DocumentInfo>) => void
  removeDocument: (id: string) => void
  setSelectedDocuments: (ids: string[]) => void
  toggleDocumentSelection: (id: string) => void
  selectAllDocuments: () => void
  clearSelection: () => void
  
  // 上传相关
  addToUploadQueue: (files: File[]) => void
  updateUploadProgress: (fileId: string, progress: Partial<UploadProgress>) => void
  removeFromUploadQueue: (fileId: string) => void
  clearUploadQueue: () => void
  
  // 过滤和排序
  setFilters: (filters: Partial<DocumentFilters>) => void
  setSorting: (sortBy: DocumentState['sortBy'], sortOrder: DocumentState['sortOrder']) => void
  
  // 分页
  setCurrentPage: (page: number) => void
  setPageSize: (size: number) => void
  
  // 文档操作
  uploadDocuments: (files: File[]) => Promise<void>
  deleteDocument: (id: string) => Promise<void>
  batchDeleteDocuments: (ids: string[]) => Promise<void>
  reprocessDocument: (id: string) => Promise<void>
  downloadDocument: (id: string) => Promise<void>
  
  // 数据加载
  loadDocuments: () => Promise<void>
  refreshDocuments: () => Promise<void>
  
  // 统计
  updateStats: () => void
  
  // 重置
  resetState: () => void
}

/**
 * 获取文档类型
 */
const getDocumentType = (fileName: string): DocumentType => {
  const extension = fileName.split('.').pop()?.toLowerCase()
  switch (extension) {
    case 'pdf':
      return DocumentType.PDF
    case 'doc':
      return DocumentType.DOC
    case 'docx':
      return DocumentType.DOCX
    case 'txt':
      return DocumentType.TXT
    case 'md':
      return DocumentType.MD
    case 'html':
    case 'htm':
      return DocumentType.HTML
    default:
      return DocumentType.OTHER
  }
}

/**
 * 格式化文件大小
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 计算统计信息
 */
const calculateStats = (documents: DocumentInfo[]): DocumentStats => {
  const stats: DocumentStats = {
    total: documents.length,
    byStatus: {
      [DocumentStatus.UPLOADING]: 0,
      [DocumentStatus.PROCESSING]: 0,
      [DocumentStatus.COMPLETED]: 0,
      [DocumentStatus.ERROR]: 0,
      [DocumentStatus.DELETED]: 0
    },
    byType: {
      [DocumentType.PDF]: 0,
      [DocumentType.DOC]: 0,
      [DocumentType.DOCX]: 0,
      [DocumentType.TXT]: 0,
      [DocumentType.MD]: 0,
      [DocumentType.HTML]: 0,
      [DocumentType.OTHER]: 0
    },
    totalSize: 0,
    averageProcessingTime: 0
  }
  
  let totalProcessingTime = 0
  let processedCount = 0
  
  documents.forEach(doc => {
    stats.byStatus[doc.status]++
    stats.byType[doc.type]++
    stats.totalSize += doc.size
    
    if (doc.processTime && doc.completedTime) {
      totalProcessingTime += doc.completedTime - doc.processTime
      processedCount++
    }
  })
  
  if (processedCount > 0) {
    stats.averageProcessingTime = totalProcessingTime / processedCount
  }
  
  return stats
}

// 规范化辅助函数，确保后端不同字段名与时间格式统一
const toMilliseconds = (input: any): number => {
  if (!input && input !== 0) return Date.now()
  if (typeof input === 'number') {
    // 如果看起来像秒，则转为毫秒
    return input < 1e12 ? Math.round(input * 1000) : Math.round(input)
  }
  if (input instanceof Date) return input.getTime()
  try {
    const d = new Date(input)
    const ms = d.getTime()
    return isNaN(ms) ? Date.now() : ms
  } catch {
    return Date.now()
  }
}

const asString = (v: any, fallback = ''): string => {
  if (typeof v === 'string') return v
  if (v === null || v === undefined) return fallback
  try { return String(v) } catch { return fallback }
}

const asNumber = (v: any, fallback = 0): number => {
  if (typeof v === 'number' && isFinite(v)) return v
  const n = Number(v)
  return isFinite(n) ? n : fallback
}

const normalizeStatus = (value: any): DocumentStatus => {
  const s = String(value ?? '').toLowerCase()
  switch (s) {
    case 'uploading': return DocumentStatus.UPLOADING
    case 'processing':
    case 'pending':
    case 'in_progress': return DocumentStatus.PROCESSING
    case 'completed':
    case 'done':
    case 'processed':
    case 'success':
    case 'ready': return DocumentStatus.COMPLETED
    case 'error':
    case 'failed':
    case 'failure': return DocumentStatus.ERROR
    case 'deleted':
    case 'removed': return DocumentStatus.DELETED
    default: return DocumentStatus.PROCESSING
  }
}

const normalizeType = (input: any, name?: string): DocumentType => {
  const s = String(input ?? '').toLowerCase()
  switch (s) {
    case 'pdf': return DocumentType.PDF
    case 'doc': return DocumentType.DOC
    case 'docx': return DocumentType.DOCX
    case 'txt': return DocumentType.TXT
    case 'md': return DocumentType.MD
    case 'html':
    case 'htm': return DocumentType.HTML
    default:
      return name ? getDocumentType(name) : DocumentType.OTHER
  }
}

const normalizeDocument = (input: any): DocumentInfo => {
  const name = input?.name ?? input?.file_name ?? input?.filename ?? input?.title ?? 'Untitled'
  const originalName = input?.originalName ?? input?.original_name ?? input?.file_name ?? input?.filename ?? name
  const uploadTimeCandidate = input?.uploadTime ?? input?.upload_time ?? input?.uploaded_at ?? input?.created_at
  const idCandidate = input?.id ?? input?.doc_id ?? input?.document_id ?? input?.uuid ?? input?._id
  const sizeCandidate = input?.size ?? input?.file_size ?? input?.length
  const typeCandidate = input?.type ?? input?.file_type ?? input?.mime ?? input?.content_type
  const processedFlag = input?.processed

  const metadataTags = Array.isArray(input?.tags ?? input?.metadata?.tags) ? (input?.tags ?? input?.metadata?.tags) : []

  return {
    id: asString(idCandidate ?? Date.now()),
    name: asString(name),
    originalName: asString(originalName),
    type: normalizeType(typeCandidate, name),
    size: asNumber(sizeCandidate, 0),
    status: normalizeStatus(input?.status ?? (processedFlag === true ? 'completed' : processedFlag === false ? 'processing' : 'processing')),
    uploadTime: toMilliseconds(uploadTimeCandidate ?? Date.now()),
    processTime: input?.process_time ? toMilliseconds(input.process_time) : undefined,
    completedTime: input?.completed_time ? toMilliseconds(input.completed_time) : undefined,
    url: input?.url ?? input?.download_url ?? undefined,
    thumbnailUrl: input?.thumbnail_url ?? undefined,
    metadata: {
      author: input?.author ?? input?.metadata?.author,
      title: input?.title ?? input?.metadata?.title,
      description: input?.description ?? input?.metadata?.description,
      tags: metadataTags,
      pageCount: input?.page_count ?? input?.pages ?? input?.metadata?.pageCount,
      wordCount: input?.word_count ?? input?.metadata?.wordCount,
      language: input?.language ?? input?.metadata?.language
    },
    processingInfo: input?.processing_info ? {
      progress: asNumber(input.processing_info.progress ?? input.progress, 0),
      stage: asString(input.processing_info.stage ?? input.stage, ''),
      message: asString(input.processing_info.message ?? input.message, '')
    } : (input?.progress || input?.stage || input?.message) ? {
      progress: asNumber(input?.progress, 0),
      stage: asString(input?.stage, ''),
      message: asString(input?.message, '')
    } : undefined,
    error: input?.error ?? undefined
  }
}

/**
 * 创建文档管理状态store
 */
export const useDocumentStore = create<DocumentState>()(persist(
  (set, get) => ({
    // 初始状态
    documents: [],
    selectedDocuments: [],
    
    uploadQueue: [],
    isUploading: false,
    
    loading: false,
    error: null,
    
    filters: {
      status: 'all',
      type: 'all',
      dateRange: 'all',
      searchQuery: '',
      tags: []
    },
    sortBy: 'uploadTime',
    sortOrder: 'desc',
    
    currentPage: 1,
    pageSize: 20,
    totalPages: 1,
    
    stats: {
      total: 0,
      byStatus: {
        [DocumentStatus.UPLOADING]: 0,
        [DocumentStatus.PROCESSING]: 0,
        [DocumentStatus.COMPLETED]: 0,
        [DocumentStatus.ERROR]: 0,
        [DocumentStatus.DELETED]: 0
      },
      byType: {
        [DocumentType.PDF]: 0,
        [DocumentType.DOC]: 0,
        [DocumentType.DOCX]: 0,
        [DocumentType.TXT]: 0,
        [DocumentType.MD]: 0,
        [DocumentType.HTML]: 0,
        [DocumentType.OTHER]: 0
      },
      totalSize: 0,
      averageProcessingTime: 0
    },
    
    // Actions
    setDocuments: (documents) => {
      const normalized = documents.map(normalizeDocument)
      const stats = calculateStats(normalized)
      const totalPages = Math.ceil(normalized.length / get().pageSize)
      set({ documents: normalized, stats, totalPages })
    },
    
    addDocument: (document) => {
      const { documents } = get()
      const normalized = normalizeDocument(document)
      const updatedDocuments = [normalized, ...documents]
      get().setDocuments(updatedDocuments)
    },
    
    updateDocument: (id, updates) => {
      const { documents } = get()
      const updatedDocuments = documents.map(doc => 
        doc.id === id ? { ...doc, ...updates } : doc
      )
      get().setDocuments(updatedDocuments)
    },
    
    removeDocument: (id) => {
      const { documents, selectedDocuments } = get()
      const updatedDocuments = documents.filter(doc => doc.id !== id)
      const updatedSelected = selectedDocuments.filter(docId => docId !== id)
      set({ selectedDocuments: updatedSelected })
      get().setDocuments(updatedDocuments)
    },
    
    setSelectedDocuments: (ids) => set({ selectedDocuments: ids }),
    
    toggleDocumentSelection: (id) => {
      const { selectedDocuments } = get()
      const isSelected = selectedDocuments.includes(id)
      const updatedSelected = isSelected
        ? selectedDocuments.filter(docId => docId !== id)
        : [...selectedDocuments, id]
      set({ selectedDocuments: updatedSelected })
    },
    
    selectAllDocuments: () => {
      const { documents } = get()
      const allIds = documents.map(doc => doc.id)
      set({ selectedDocuments: allIds })
    },
    
    clearSelection: () => set({ selectedDocuments: [] }),
    
    addToUploadQueue: (files) => {
      const { uploadQueue } = get()
      const newUploads: UploadProgress[] = files.map(file => ({
        fileId: `${Date.now()}-${Math.random()}`,
        fileName: file.name,
        progress: 0,
        speed: 0,
        remainingTime: 0,
        status: 'uploading'
      }))
      set({ uploadQueue: [...uploadQueue, ...newUploads], isUploading: true })
    },
    
    updateUploadProgress: (fileId, progress) => {
      const { uploadQueue } = get()
      const updatedQueue = uploadQueue.map(upload => 
        upload.fileId === fileId ? { ...upload, ...progress } : upload
      )
      set({ uploadQueue: updatedQueue })
    },
    
    removeFromUploadQueue: (fileId) => {
      const { uploadQueue } = get()
      const updatedQueue = uploadQueue.filter(upload => upload.fileId !== fileId)
      set({ 
        uploadQueue: updatedQueue, 
        isUploading: updatedQueue.some(upload => upload.status === 'uploading')
      })
    },
    
    clearUploadQueue: () => set({ uploadQueue: [], isUploading: false }),
    
    setFilters: (filters) => {
      const currentFilters = get().filters
      set({ filters: { ...currentFilters, ...filters }, currentPage: 1 })
    },
    
    setSorting: (sortBy, sortOrder) => set({ sortBy, sortOrder }),
    
    setCurrentPage: (currentPage) => set({ currentPage }),
    
    setPageSize: (pageSize) => {
      const { documents } = get()
      const totalPages = Math.ceil(documents.length / pageSize)
      set({ pageSize, totalPages, currentPage: 1 })
    },
    
    uploadDocuments: async (files) => {
      set({ loading: true, error: null })
      
      try {
        get().addToUploadQueue(files)
        
        // 为每个文件创建临时文档记录
        const tempDocuments: DocumentInfo[] = files.map(file => {
          const fileId = `temp-${Date.now()}-${Math.random()}`
          return {
            id: fileId,
            name: file.name.split('.')[0],
            originalName: file.name,
            type: getDocumentType(file.name),
            size: file.size,
            status: DocumentStatus.UPLOADING,
            uploadTime: Date.now(),
            metadata: {
              tags: []
            }
          }
        })
        
        // 添加临时文档到列表
        tempDocuments.forEach(doc => get().addDocument(doc))
        
        // 调用上传API
        const response = await documentsApi.uploadDocuments(
          files,
          { uploadedBy: 'user' },
          (progress) => {
            // 更新所有文件的上传进度
            tempDocuments.forEach(doc => {
              get().updateUploadProgress(doc.id, { progress })
            })
          }
        )
        
        if (!response.success || !response.data) {
          throw new Error(response.error || '上传失败')
        }
        
        const { documents: uploadedDocs, failed } = response.data
        
        // 移除临时文档
        tempDocuments.forEach(doc => {
          get().removeDocument(doc.id)
          get().removeFromUploadQueue(doc.id)
        })
        
        // 添加成功上传的文档
        uploadedDocs.forEach(doc => get().addDocument(doc))
        
        // 处理失败的文件
        if (failed.length > 0) {
          const failedNames = failed.map(f => f.filename).join(', ')
          set({ error: `部分文件上传失败: ${failedNames}` })
        }
        
        // 刷新文档列表
        await get().loadDocuments()
        
      } catch (error: any) {
        const errorMessage = error?.error || error?.message || '文档上传失败，请稍后重试'
        set({ error: errorMessage })
        console.error('上传错误:', error)
      } finally {
        set({ loading: false })
      }
    },
    
    deleteDocument: async (id) => {
      set({ loading: true, error: null })
      
      try {
        const response = await documentsApi.deleteDocument(id)
        
        if (!response.success) {
          throw new Error(response.error || '删除失败')
        }
        
        get().removeDocument(id)
        
      } catch (error: any) {
        const errorMessage = error?.error || error?.message || '删除文档失败，请稍后重试'
        set({ error: errorMessage })
        console.error('删除错误:', error)
      } finally {
        set({ loading: false })
      }
    },
    
    batchDeleteDocuments: async (ids) => {
      set({ loading: true, error: null })
      
      try {
        const response = await documentsApi.batchDeleteDocuments(ids)
        
        if (!response.success || !response.data) {
          throw new Error(response.error || '批量删除失败')
        }
        
        const { deleted, failed } = response.data
        
        // 移除成功删除的文档
        deleted.forEach(id => get().removeDocument(id))
        
        // 处理删除失败的文档
        if (failed.length > 0) {
          const failedIds = failed.map(f => f.id).join(', ')
          set({ error: `部分文档删除失败: ${failedIds}` })
        }
        
        get().clearSelection()
        
      } catch (error: any) {
        const errorMessage = error?.error || error?.message || '批量删除失败，请稍后重试'
        set({ error: errorMessage })
        console.error('批量删除错误:', error)
      } finally {
        set({ loading: false })
      }
    },
    
    reprocessDocument: async (id) => {
      set({ loading: true, error: null })
      
      try {
        get().updateDocument(id, { 
          status: DocumentStatus.PROCESSING,
          processTime: Date.now()
        })
        
        const response = await documentsApi.reprocessDocument(id)
        
        if (!response.success) {
          throw new Error(response.error || '重新处理失败')
        }
        
        // 重新加载文档信息
        const docResponse = await documentsApi.getDocument(id)
        if (docResponse.success && docResponse.data) {
          get().updateDocument(id, docResponse.data)
        }
        
      } catch (error: any) {
        get().updateDocument(id, { 
          status: DocumentStatus.ERROR,
          error: '重新处理失败'
        })
        const errorMessage = error?.error || error?.message || '重新处理失败，请稍后重试'
        set({ error: errorMessage })
        console.error('重新处理错误:', error)
      } finally {
        set({ loading: false })
      }
    },
    
    downloadDocument: async (id) => {
      try {
        const documentInfo = get().documents.find(doc => doc.id === id)
        if (!documentInfo) {
          throw new Error('文档不存在')
        }
        
        const blob = await documentsApi.downloadDocument(id)
        
        // 创建下载链接
        const url = window.URL.createObjectURL(blob)
        const link = window.document.createElement('a')
        link.href = url
        link.download = documentInfo.originalName
        window.document.body.appendChild(link)
        link.click()
        
        // 清理
        window.document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
      } catch (error: any) {
        const errorMessage = error?.error || error?.message || '下载失败，请稍后重试'
        set({ error: errorMessage })
        console.error('下载错误:', error)
      }
    },
    
    loadDocuments: async () => {
      set({ loading: true, error: null })
      
      try {
        const { filters, sortBy, sortOrder, currentPage, pageSize } = get()
        
        // 构建查询参数
        const apiSortBy = sortBy === 'uploadTime' ? 'date' : 
                         sortBy === 'status' ? 'type' : sortBy
        
        const params = {
          page: currentPage,
          limit: pageSize,
          search: filters.searchQuery || undefined,
          type: filters.type !== 'all' ? filters.type : undefined,
          status: filters.status !== 'all' ? filters.status : undefined,
          tags: filters.tags.length > 0 ? filters.tags : undefined,
          sortBy: apiSortBy as 'name' | 'type' | 'date' | 'size',
          sortOrder
        }
        
        const response = await documentsApi.getDocuments(params)
        
        if (!response.success || !response.data) {
          throw new Error(response.error || '获取文档列表失败')
        }
        
        const { documents, totalPages } = response.data
        
        // 统一映射，确保uploadTime为有效毫秒
        const normalizedDocs = documents.map(normalizeDocument)
        get().setDocuments(normalizedDocs)
        set({ totalPages })
        
        // 更新统计信息
        get().updateStats()
        
      } catch (error: any) {
        const errorMessage = error?.error || error?.message || '加载文档列表失败，请稍后重试'
        set({ error: errorMessage })
        console.error('加载错误:', error)
      } finally {
        set({ loading: false })
      }
    },
    
    refreshDocuments: async () => {
      await get().loadDocuments()
    },
    
    updateStats: () => {
      const { documents } = get()
      const stats = calculateStats(documents)
      set({ stats })
    },
    
    resetState: () => {
      set({
        documents: [],
        selectedDocuments: [],
        uploadQueue: [],
        isUploading: false,
        loading: false,
        error: null,
        currentPage: 1
      })
    }
  }),
  {
    name: 'document-store',
    partialize: (state) => ({
      filters: state.filters,
      sortBy: state.sortBy,
      sortOrder: state.sortOrder,
      pageSize: state.pageSize
    })
  }
))

/**
 * 文档store的hook
 */
export const useDocuments = () => {
  const store = useDocumentStore()
  return {
    ...store,
    // 便捷方法
    hasDocuments: store.documents.length > 0,
    hasSelection: store.selectedDocuments.length > 0,
    isAllSelected: store.selectedDocuments.length === store.documents.length,
    completedDocuments: store.documents.filter(doc => doc.status === DocumentStatus.COMPLETED),
    processingDocuments: store.documents.filter(doc => doc.status === DocumentStatus.PROCESSING),
    errorDocuments: store.documents.filter(doc => doc.status === DocumentStatus.ERROR)
  }
}