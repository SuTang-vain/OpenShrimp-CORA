import * as React from 'react'
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  History,
  Search,
  Clock,
  Trash2,
  Star,
  StarOff,
  Filter,
  SortAsc,
  SortDesc,
  Tag,
  Copy
} from 'lucide-react'
import { toast } from 'sonner'
import { format, isToday, isYesterday, isThisWeek } from 'date-fns'
import { zhCN } from 'date-fns/locale'

import { cn } from '@/utils/cn'

/**
 * 搜索历史项接口
 */
export interface SearchHistoryItem {
  id: string
  query: string
  timestamp: string
  resultCount: number
  duration: number
  sources: string[]
  mode: string
  isFavorite?: boolean
  tags?: string[]
  metadata?: Record<string, any>
}

/**
 * 搜索历史组件属性接口
 */
interface SearchHistoryProps {
  onItemClick?: (item: SearchHistoryItem) => void
  onItemDelete?: (itemId: string) => void
  onClearAll?: () => void
  maxItems?: number
  showFilters?: boolean
  className?: string
}

/**
 * 排序选项
 */
type SortOption = 'time' | 'query' | 'results' | 'duration'
type SortOrder = 'asc' | 'desc'

/**
 * 过滤选项
 */
interface FilterOptions {
  timeRange: 'all' | 'today' | 'week' | 'month'
  mode: 'all' | 'semantic' | 'hybrid' | 'keyword'
  favorites: boolean
  minResults: number
}

/**
 * 模拟搜索历史数据
 */
const mockHistoryData: SearchHistoryItem[] = [
  {
    id: '1',
    query: '人工智能的发展历程',
    timestamp: new Date().toISOString(),
    resultCount: 15,
    duration: 1200,
    sources: ['学术论文', '新闻报道'],
    mode: 'semantic',
    isFavorite: true,
    tags: ['AI', '技术']
  },
  {
    id: '2',
    query: 'React Hooks 最佳实践',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    resultCount: 8,
    duration: 800,
    sources: ['技术文档', '博客'],
    mode: 'hybrid',
    isFavorite: false,
    tags: ['React', '前端']
  },
  {
    id: '3',
    query: '机器学习算法比较',
    timestamp: new Date(Date.now() - 86400000).toISOString(),
    resultCount: 22,
    duration: 1500,
    sources: ['学术论文', '教程'],
    mode: 'semantic',
    isFavorite: true,
    tags: ['机器学习', '算法']
  },
  {
    id: '4',
    query: 'TypeScript 类型系统',
    timestamp: new Date(Date.now() - 172800000).toISOString(),
    resultCount: 12,
    duration: 950,
    sources: ['官方文档', '社区'],
    mode: 'keyword',
    isFavorite: false,
    tags: ['TypeScript', '编程']
  },
  {
    id: '5',
    query: '深度学习框架对比',
    timestamp: new Date(Date.now() - 259200000).toISOString(),
    resultCount: 18,
    duration: 1300,
    sources: ['技术博客', '官方文档'],
    mode: 'hybrid',
    isFavorite: false,
    tags: ['深度学习', '框架']
  }
]

/**
 * 格式化时间显示
 */
const formatTimeDisplay = (timestamp: string): string => {
  const date = new Date(timestamp)
  
  if (isToday(date)) {
    return `今天 ${format(date, 'HH:mm', { locale: zhCN })}`
  }
  
  if (isYesterday(date)) {
    return `昨天 ${format(date, 'HH:mm', { locale: zhCN })}`
  }
  
  if (isThisWeek(date)) {
    return format(date, 'EEEE HH:mm', { locale: zhCN })
  }
  
  return format(date, 'MM-dd HH:mm', { locale: zhCN })
}

/**
 * 格式化持续时间
 */
const formatDuration = (ms: number): string => {
  if (ms < 1000) {
    return `${ms}ms`
  }
  return `${(ms / 1000).toFixed(1)}s`
}

/**
 * 获取模式显示名称
 */
const getModeDisplayName = (mode: string): string => {
  const modeMap: Record<string, string> = {
    semantic: '语义搜索',
    hybrid: '混合搜索',
    keyword: '关键词搜索',
    vector: '向量搜索'
  }
  return modeMap[mode] || mode
}

/**
 * 获取模式颜色
 */
const getModeColor = (mode: string): string => {
  const colorMap: Record<string, string> = {
    semantic: 'bg-blue-100 text-blue-800',
    hybrid: 'bg-purple-100 text-purple-800',
    keyword: 'bg-green-100 text-green-800',
    vector: 'bg-orange-100 text-orange-800'
  }
  return colorMap[mode] || 'bg-gray-100 text-gray-800'
}

/**
 * 搜索历史组件
 * 显示和管理用户的搜索历史记录
 */
const SearchHistory: React.FC<SearchHistoryProps> = ({
  onItemClick,
  onItemDelete,
  onClearAll,
  maxItems = 50,
  showFilters = true,
  className
}) => {
  const [historyItems, setHistoryItems] = useState<SearchHistoryItem[]>(mockHistoryData)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<SortOption>('time')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')
  const [showFilterPanel, setShowFilterPanel] = useState(false)
  const [filters, setFilters] = useState<FilterOptions>({
    timeRange: 'all',
    mode: 'all',
    favorites: false,
    minResults: 0
  })
  
  /**
   * 过滤和排序历史记录
   */
  const filteredAndSortedItems = React.useMemo(() => {
    const filtered = historyItems.filter(item => {
      // 搜索过滤
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        const matchesQuery = item.query.toLowerCase().includes(query)
        const matchesTags = item.tags?.some(tag => tag.toLowerCase().includes(query))
        if (!matchesQuery && !matchesTags) {
          return false
        }
      }
      
      // 时间范围过滤
      if (filters.timeRange !== 'all') {
        const itemDate = new Date(item.timestamp)
        const now = new Date()
        
        switch (filters.timeRange) {
          case 'today':
            if (!isToday(itemDate)) return false
            break
          case 'week':
            if (!isThisWeek(itemDate)) return false
            break
          case 'month': {
            const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
            if (itemDate < monthAgo) return false
            break
          }
        }
      }
      
      // 模式过滤
      if (filters.mode !== 'all' && item.mode !== filters.mode) {
        return false
      }
      
      // 收藏过滤
      if (filters.favorites && !item.isFavorite) {
        return false
      }
      
      // 最小结果数过滤
      if (item.resultCount < filters.minResults) {
        return false
      }
      
      return true
    })
    
    // 排序
    filtered.sort((a, b) => {
      let aValue: any
      let bValue: any
      
      switch (sortBy) {
        case 'time':
          aValue = new Date(a.timestamp)
          bValue = new Date(b.timestamp)
          break
        case 'query':
          aValue = a.query.toLowerCase()
          bValue = b.query.toLowerCase()
          break
        case 'results':
          aValue = a.resultCount
          bValue = b.resultCount
          break
        case 'duration':
          aValue = a.duration
          bValue = b.duration
          break
        default:
          return 0
      }
      
      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1
      return 0
    })
    
    return filtered.slice(0, maxItems)
  }, [historyItems, searchQuery, sortBy, sortOrder, filters, maxItems])
  
  /**
   * 切换收藏状态
   */
  const toggleFavorite = (itemId: string) => {
    setHistoryItems(prev => prev.map(item => 
      item.id === itemId 
        ? { ...item, isFavorite: !item.isFavorite }
        : item
    ))
  }
  
  /**
   * 删除历史记录项
   */
  const deleteItem = (itemId: string) => {
    setHistoryItems(prev => prev.filter(item => item.id !== itemId))
    onItemDelete?.(itemId)
    toast.success('已删除历史记录')
  }
  
  /**
   * 清空所有历史记录
   */
  const clearAllItems = () => {
    setHistoryItems([])
    onClearAll?.()
    toast.success('已清空所有历史记录')
  }
  
  /**
   * 复制查询文本
   */
  const copyQuery = (query: string) => {
    navigator.clipboard.writeText(query)
    toast.success('查询已复制到剪贴板')
  }
  
  /**
   * 切换排序
   */
  const toggleSort = (field: SortOption) => {
    if (sortBy === field) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('desc')
    }
  }
  
  return (
    <div className={cn('bg-white border border-gray-200 rounded-lg shadow-sm', className)}>
      {/* 头部 */}
      <div className="flex items-center justify-between p-4 border-b border-gray-100">
        <div className="flex items-center space-x-2">
          <History className="w-5 h-5 text-gray-500" />
          <h3 className="text-lg font-semibold text-gray-900">
            搜索历史
          </h3>
          <span className="text-sm text-gray-500">
            ({filteredAndSortedItems.length})
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          {showFilters && (
            <button
              onClick={() => setShowFilterPanel(!showFilterPanel)}
              className={cn(
                'p-2 rounded-md transition-colors',
                'hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500',
                showFilterPanel && 'bg-blue-50 text-blue-600'
              )}
            >
              <Filter className="w-4 h-4" />
            </button>
          )}
          
          {historyItems.length > 0 && (
            <button
              onClick={clearAllItems}
              className="p-2 rounded-md text-red-600 hover:bg-red-50 transition-colors"
              title="清空所有历史记录"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
      
      {/* 过滤器面板 */}
      <AnimatePresence>
        {showFilterPanel && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-b border-gray-100 p-4 bg-gray-50"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  时间范围
                </label>
                <select
                  value={filters.timeRange}
                  onChange={(e) => setFilters(prev => ({ ...prev, timeRange: e.target.value as any }))}
                  className="w-full text-sm border border-gray-300 rounded-md px-2 py-1"
                >
                  <option value="all">全部时间</option>
                  <option value="today">今天</option>
                  <option value="week">本周</option>
                  <option value="month">本月</option>
                </select>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  搜索模式
                </label>
                <select
                  value={filters.mode}
                  onChange={(e) => setFilters(prev => ({ ...prev, mode: e.target.value as any }))}
                  className="w-full text-sm border border-gray-300 rounded-md px-2 py-1"
                >
                  <option value="all">全部模式</option>
                  <option value="semantic">语义搜索</option>
                  <option value="hybrid">混合搜索</option>
                  <option value="keyword">关键词搜索</option>
                </select>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  最小结果数
                </label>
                <input
                  type="number"
                  min="0"
                  value={filters.minResults}
                  onChange={(e) => setFilters(prev => ({ ...prev, minResults: parseInt(e.target.value) || 0 }))}
                  className="w-full text-sm border border-gray-300 rounded-md px-2 py-1"
                />
              </div>
              
              <div className="flex items-end">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={filters.favorites}
                    onChange={(e) => setFilters(prev => ({ ...prev, favorites: e.target.checked }))}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm text-gray-700">仅显示收藏</span>
                </label>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* 搜索框 */}
      <div className="p-4 border-b border-gray-100">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="搜索历史记录..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>
      
      {/* 排序控制 */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-100">
        <div className="flex items-center space-x-4 text-xs">
          <button
            onClick={() => toggleSort('time')}
            className={cn(
              'flex items-center space-x-1 hover:text-blue-600',
              sortBy === 'time' && 'text-blue-600 font-medium'
            )}
          >
            <Clock className="w-3 h-3" />
            <span>时间</span>
            {sortBy === 'time' && (
              sortOrder === 'asc' ? <SortAsc className="w-3 h-3" /> : <SortDesc className="w-3 h-3" />
            )}
          </button>
          
          <button
            onClick={() => toggleSort('results')}
            className={cn(
              'flex items-center space-x-1 hover:text-blue-600',
              sortBy === 'results' && 'text-blue-600 font-medium'
            )}
          >
            <span>结果数</span>
            {sortBy === 'results' && (
              sortOrder === 'asc' ? <SortAsc className="w-3 h-3" /> : <SortDesc className="w-3 h-3" />
            )}
          </button>
          
          <button
            onClick={() => toggleSort('duration')}
            className={cn(
              'flex items-center space-x-1 hover:text-blue-600',
              sortBy === 'duration' && 'text-blue-600 font-medium'
            )}
          >
            <span>耗时</span>
            {sortBy === 'duration' && (
              sortOrder === 'asc' ? <SortAsc className="w-3 h-3" /> : <SortDesc className="w-3 h-3" />
            )}
          </button>
        </div>
      </div>
      
      {/* 历史记录列表 */}
      <div className="max-h-96 overflow-y-auto">
        {filteredAndSortedItems.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <History className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p className="text-sm">
              {searchQuery || Object.values(filters).some(v => v !== 'all' && v !== false && v !== 0)
                ? '没有找到匹配的历史记录'
                : '暂无搜索历史'
              }
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {filteredAndSortedItems.map((item, index) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="p-4 hover:bg-gray-50 transition-colors group"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0 cursor-pointer" onClick={() => onItemClick?.(item)}>
                    <div className="flex items-center space-x-2 mb-1">
                      <h4 className="text-sm font-medium text-gray-900 truncate">
                        {item.query}
                      </h4>
                      {item.isFavorite && (
                        <Star className="w-3 h-3 text-yellow-500 fill-current" />
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-4 text-xs text-gray-500 mb-2">
                      <span className="flex items-center space-x-1">
                        <Clock className="w-3 h-3" />
                        <span>{formatTimeDisplay(item.timestamp)}</span>
                      </span>
                      
                      <span>{item.resultCount} 个结果</span>
                      <span>{formatDuration(item.duration)}</span>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <span className={cn(
                        'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                        getModeColor(item.mode)
                      )}>
                        {getModeDisplayName(item.mode)}
                      </span>
                      
                      {item.tags && item.tags.map(tag => (
                        <span
                          key={tag}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-700"
                        >
                          <Tag className="w-2 h-2 mr-1" />
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  {/* 操作按钮 */}
                  <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => toggleFavorite(item.id)}
                      className="p-1 hover:bg-gray-200 rounded transition-colors"
                      title={item.isFavorite ? '取消收藏' : '添加收藏'}
                    >
                      {item.isFavorite ? (
                        <Star className="w-3 h-3 text-yellow-500 fill-current" />
                      ) : (
                        <StarOff className="w-3 h-3 text-gray-400" />
                      )}
                    </button>
                    
                    <button
                      onClick={() => copyQuery(item.query)}
                      className="p-1 hover:bg-gray-200 rounded transition-colors"
                      title="复制查询"
                    >
                      <Copy className="w-3 h-3 text-gray-400" />
                    </button>
                    
                    <button
                      onClick={() => deleteItem(item.id)}
                      className="p-1 hover:bg-red-100 rounded transition-colors"
                      title="删除记录"
                    >
                      <Trash2 className="w-3 h-3 text-red-400" />
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default SearchHistory
export type { SearchHistoryProps }