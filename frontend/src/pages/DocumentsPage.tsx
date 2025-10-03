import React, { useState, useEffect } from 'react'
// import { motion, AnimatePresence } from 'framer-motion'
import {
  Upload,
  FileText,
  Search,
  Filter,
  MoreVertical,
  Download,
  Trash2,
  Edit3,
  Eye,
  Clock,
  User,
  Tag,
  CheckCircle,
  AlertCircle,
  Loader2,
  Plus,
  Grid3X3,
  List,
  SortAsc,
  SortDesc,
  X,
} from 'lucide-react'
import { toast } from 'sonner'
import { format } from 'date-fns'

import { cn } from '@/utils/cn'
import { useDocuments, DocumentStatus } from '@/stores/documentStore'
import DocumentUpload from '@/components/documents/DocumentUpload'

/**
 * 视图模式类型
 */
type ViewMode = 'grid' | 'list'

/**
 * 排序字段类型
 */
type SortField = 'name' | 'date' | 'size' | 'status'

/**
 * 文档过滤器接口
 */
interface DocumentFilters {
  status: DocumentStatus | 'all'
  fileType: string
  dateRange: string
  tags: string[]
}

/**
 * 文档管理页面组件
 * 提供文档上传、管理和查看功能
 */
const DocumentsPage: React.FC = () => {
  // 使用文档store
  const {
    documents,
    loading,
    selectedDocuments,
    loadDocuments,
    deleteDocument,
    batchDeleteDocuments,
    toggleDocumentSelection
  } = useDocuments()
  
  // UI 状态
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [showUpload, setShowUpload] = useState(false)
  const [sortField, setSortField] = useState<SortField>('date')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  
  // 过滤器状态
  const [filters, setFilters] = useState<DocumentFilters>({
    status: 'all',
    fileType: 'all',
    dateRange: 'all',
    tags: [],
  })

  // 初始化加载文档
  useEffect(() => {
    loadDocuments()
  }, [loadDocuments])

  /**
   * 处理文档上传完成
   */
  const handleUploadComplete = (files: File[]) => {
    toast.success(`成功上传 ${files.length} 个文件`)
    setShowUpload(false)
  }

  /**
   * 处理文档上传错误
   */
  const handleUploadError = (error: string) => {
    toast.error(error)
  }

  /**
   * 处理文档删除
   */
  const handleDeleteDocument = async (docId: string) => {
    try {
      await deleteDocument(docId)
      toast.success('文档已删除')
    } catch (error) {
      toast.error('删除失败，请重试')
    }
  }

  /**
   * 处理批量删除
   */
  const handleBatchDelete = async () => {
    if (selectedDocuments.length === 0) return
    
    try {
      await batchDeleteDocuments(selectedDocuments)
      toast.success(`已删除 ${selectedDocuments.length} 个文档`)
    } catch (error) {
      toast.error('批量删除失败，请重试')
    }
  }

  /**
   * 过滤和排序文档
   */
  const filteredAndSortedDocuments = React.useMemo(() => {
    const filtered = documents.filter(doc => {
      // 搜索过滤
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        const matchesName = doc.name.toLowerCase().includes(query)
        const matchesTitle = doc.metadata?.title?.toLowerCase().includes(query)
        const matchesTags = doc.metadata?.tags?.some(tag => tag.toLowerCase().includes(query))
        if (!matchesName && !matchesTitle && !matchesTags) {
          return false
        }
      }
      
      // 状态过滤
      if (filters.status !== 'all' && doc.status !== filters.status) {
        return false
      }
      
      // 文件类型过滤
      if (filters.fileType !== 'all') {
        const fileExt = doc.name.split('.').pop()?.toLowerCase()
        if (fileExt !== filters.fileType) {
          return false
        }
      }
      
      // 标签过滤
      if (filters.tags.length > 0) {
        const hasMatchingTag = filters.tags.some(tag => 
          doc.metadata?.tags?.includes(tag)
        )
        if (!hasMatchingTag) {
          return false
        }
      }
      
      return true
    })
    
    // 排序
    filtered.sort((a, b) => {
      let aValue: any
      let bValue: any
      
      switch (sortField) {
        case 'name':
          aValue = a.name.toLowerCase()
          bValue = b.name.toLowerCase()
          break
        case 'date':
          aValue = new Date(a.uploadTime)
          bValue = new Date(b.uploadTime)
          break
        case 'size':
          aValue = a.size
          bValue = b.size
          break
        case 'status':
          aValue = a.status
          bValue = b.status
          break
        default:
          return 0
      }
      
      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1
      return 0
    })
    
    return filtered
  }, [documents, searchQuery, filters, sortField, sortOrder])

  /**
   * 获取状态图标
   */
  const getStatusIcon = (status: DocumentStatus) => {
    switch (status) {
      case DocumentStatus.COMPLETED:
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case DocumentStatus.PROCESSING:
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
      case DocumentStatus.ERROR:
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />
    }
  }

  /**
   * 获取状态文本
   */
  const getStatusText = (status: DocumentStatus) => {
    switch (status) {
      case DocumentStatus.UPLOADING:
        return '已上传'
      case DocumentStatus.PROCESSING:
        return '处理中'
      case DocumentStatus.COMPLETED:
        return '已处理'
      case DocumentStatus.ERROR:
        return '处理失败'
      default:
        return '未知状态'
    }
  }

  /**
   * 格式化文件大小
   */
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }



  /**
   * 切换文档选择状态
   */
  const toggleDocSelection = (docId: string) => {
    toggleDocumentSelection(docId)
  }

  /**
   * 全选/取消全选
   */
  const handleSelectAll = () => {
    if (selectedDocuments.length === filteredAndSortedDocuments.length) {
      // 清空所有选择
      filteredAndSortedDocuments.forEach(doc => {
        if (selectedDocuments.includes(doc.id)) {
          toggleDocumentSelection(doc.id)
        }
      })
    } else {
      // 选择所有文档
      filteredAndSortedDocuments.forEach(doc => {
        if (!selectedDocuments.includes(doc.id)) {
          toggleDocumentSelection(doc.id)
        }
      })
    }
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* 页面头部 */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">文档管理</h1>
          <p className="text-muted-foreground">
            管理您的文档，支持多种格式的智能处理和搜索
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          {selectedDocuments.length > 0 && (
            <button
              onClick={handleBatchDelete}
              className="btn btn-destructive btn-sm"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              删除选中 ({selectedDocuments.length})
            </button>
          )}
        </div>
      </div>

      {/* 文档上传组件 */}
      {showUpload && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">上传文档</h3>
              <button
                onClick={() => setShowUpload(false)}
                className="btn btn-ghost btn-sm"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            
            <DocumentUpload
              onUploadComplete={handleUploadComplete}
              onUploadError={handleUploadError}
            />
          </div>
        </div>
      )}

      {/* 上传区域 */}
      <div className="mb-8">
        <div
          className={cn(
            'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
            'border-border hover:border-primary/50 hover:bg-muted/50'
          )}
          onClick={() => setShowUpload(true)}
        >
          <div className="flex flex-col items-center space-y-4">
            <Upload className="h-12 w-12 text-muted-foreground" />
            
            <div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                拖拽文件到此处或点击上传
              </h3>
              <p className="text-sm text-muted-foreground">
                支持 PDF, Word, TXT, Markdown 格式，最大 50MB
              </p>
            </div>
            
            <button className="btn btn-primary btn-md">
              <Plus className="h-4 w-4 mr-2" />
              选择文件
            </button>
          </div>
        </div>
      </div>

      {/* 工具栏 */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0 mb-6">
        {/* 搜索和过滤 */}
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="搜索文档..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input pl-10 w-64"
            />
          </div>
          
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              'btn btn-outline btn-sm',
              showFilters && 'bg-accent'
            )}
          >
            <Filter className="h-4 w-4 mr-2" />
            过滤器
          </button>
        </div>
        
        {/* 视图和排序控制 */}
        <div className="flex items-center space-x-4">
          {/* 全选 */}
          {filteredAndSortedDocuments.length > 0 && (
            <button
            onClick={handleSelectAll}
            className="btn btn-outline btn-sm"
          >
            {selectedDocuments.length === filteredAndSortedDocuments.length
              ? '取消全选'
              : '全选'
            }
          </button>
          )}
          
          {/* 排序 */}
          <select
            value={sortField}
            onChange={(e) => setSortField(e.target.value as SortField)}
            className="input text-sm"
          >
            <option value="date">按日期</option>
            <option value="name">按名称</option>
            <option value="size">按大小</option>
            <option value="status">按状态</option>
          </select>
          
          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="btn btn-outline btn-sm"
          >
            {sortOrder === 'asc' ? (
              <SortAsc className="h-4 w-4" />
            ) : (
              <SortDesc className="h-4 w-4" />
            )}
          </button>
          
          {/* 视图切换 */}
          <div className="flex items-center border rounded-lg">
            <button
              onClick={() => setViewMode('grid')}
              className={cn(
                'p-2 rounded-l-lg',
                viewMode === 'grid'
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted'
              )}
            >
              <Grid3X3 className="h-4 w-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={cn(
                'p-2 rounded-r-lg',
                viewMode === 'list'
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted'
              )}
            >
              <List className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* 过滤器面板 */}
      {showFilters && (
        <div className="card p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">状态</label>
                <select
                  value={filters.status}
                  onChange={(e) => setFilters({ ...filters, status: e.target.value as any })}
                  className="input w-full"
                >
                  <option value="all">全部状态</option>
                  <option value="uploaded">已上传</option>
                  <option value="processing">处理中</option>
                  <option value="processed">已处理</option>
                  <option value="failed">处理失败</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">文件类型</label>
                <select
                  value={filters.fileType}
                  onChange={(e) => setFilters({ ...filters, fileType: e.target.value })}
                  className="input w-full"
                >
                  <option value="all">全部类型</option>
                  <option value="pdf">PDF</option>
                  <option value="docx">Word</option>
                  <option value="txt">文本</option>
                  <option value="md">Markdown</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">时间范围</label>
                <select
                  value={filters.dateRange}
                  onChange={(e) => setFilters({ ...filters, dateRange: e.target.value })}
                  className="input w-full"
                >
                  <option value="all">全部时间</option>
                  <option value="today">今天</option>
                  <option value="week">本周</option>
                  <option value="month">本月</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">标签</label>
                <div className="flex flex-wrap gap-2">
                  {['AI', '技术', '产品', '设计', '架构'].map(tag => (
                    <button
                      key={tag}
                      onClick={() => {
                        const newTags = filters.tags.includes(tag)
                          ? filters.tags.filter(t => t !== tag)
                          : [...filters.tags, tag]
                        setFilters({ ...filters, tags: newTags })
                      }}
                      className={cn(
                        'badge text-xs cursor-pointer',
                        filters.tags.includes(tag)
                          ? 'badge-default'
                          : 'badge-outline'
                      )}
                    >
                      {tag}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

      {/* 文档列表 */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
            <p className="text-muted-foreground">加载文档中...</p>
          </div>
        </div>
      ) : filteredAndSortedDocuments.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-medium mb-2">暂无文档</h3>
          <p className="text-muted-foreground mb-4">
            {searchQuery || filters.status !== 'all' || filters.fileType !== 'all'
              ? '没有找到符合条件的文档'
              : '开始上传您的第一个文档'
            }
          </p>
        </div>
      ) : (
        <div
          className={cn(
            viewMode === 'grid'
              ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6'
              : 'space-y-4'
          )}
        >
          {filteredAndSortedDocuments.map((doc) => (
            <div
              key={doc.id}
              className={cn(
                'card p-4 hover:shadow-md transition-shadow cursor-pointer',
                selectedDocuments.includes(doc.id) && 'ring-2 ring-primary',
                viewMode === 'list' && 'flex items-center space-x-4'
              )}
              onClick={() => toggleDocSelection(doc.id)}
            >
              {viewMode === 'grid' ? (
                // 网格视图
                <>
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <FileText className="h-5 w-5 text-primary" />
                      {getStatusIcon(doc.status)}
                    </div>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        // 显示更多操作菜单
                      }}
                      className="btn btn-ghost btn-sm"
                    >
                      <MoreVertical className="h-4 w-4" />
                    </button>
                  </div>
                  
                  <h3 className="font-semibold text-foreground mb-2 line-clamp-2">
                    {doc.metadata?.title || doc.name}
                  </h3>
                  
                  <div className="text-sm text-muted-foreground mb-3">
                    <div className="flex items-center justify-between mb-1">
                      <span>{formatFileSize(doc.size)}</span>
                      <span>{getStatusText(doc.status)}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Clock className="h-3 w-3" />
                      <span>{format(new Date(doc.uploadTime), 'MM/dd HH:mm')}</span>
                    </div>
                  </div>
                  
                  {doc.metadata?.tags && doc.metadata.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {doc.metadata.tags.slice(0, 3).map((tag: string, index: number) => (
                        <span key={index} className="badge badge-secondary text-xs">
                          {tag}
                        </span>
                      ))}
                      {doc.metadata.tags.length > 3 && (
                        <span className="text-xs text-muted-foreground">
                          +{doc.metadata.tags.length - 3}
                        </span>
                      )}
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          // 查看文档
                        }}
                        className="btn btn-ghost btn-sm"
                        title="查看"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          // 编辑文档
                        }}
                        className="btn btn-ghost btn-sm"
                        title="编辑"
                      >
                        <Edit3 className="h-4 w-4" />
                      </button>
                    </div>
                    
                    <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteDocument(doc.id)
                        }}
                        className="btn btn-ghost btn-sm text-destructive"
                        title="删除"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                  </div>
                </>
              ) : (
                // 列表视图
                <>
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={selectedDocuments.includes(doc.id)}
                      onChange={() => toggleDocSelection(doc.id)}
                      className="rounded"
                    />
                    <FileText className="h-5 w-5 text-primary flex-shrink-0" />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-foreground truncate">
                      {doc.metadata?.title || doc.name}
                    </h3>
                    <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                      <span>{formatFileSize(doc.size)}</span>
                      <span>{format(new Date(doc.uploadTime), 'yyyy/MM/dd HH:mm')}</span>
                      {doc.metadata?.author && (
                        <span className="flex items-center space-x-1">
                          <User className="h-3 w-3" />
                          <span>{doc.metadata.author}</span>
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(doc.status)}
                      <span className="text-sm text-muted-foreground">
                        {getStatusText(doc.status)}
                      </span>
                    </div>
                    
                    {doc.metadata?.tags && doc.metadata.tags.length > 0 && (
                      <div className="flex items-center space-x-1">
                        <Tag className="h-3 w-3 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">
                          {doc.metadata.tags.length}
                        </span>
                      </div>
                    )}
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          // 查看文档
                        }}
                        className="btn btn-ghost btn-sm"
                        title="查看"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          // 下载文档
                        }}
                        className="btn btn-ghost btn-sm"
                        title="下载"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteDocument(doc.id)
                        }}
                        className="btn btn-ghost btn-sm text-destructive"
                        title="删除"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default DocumentsPage