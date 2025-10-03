import * as React from 'react'
import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
// import { motion, AnimatePresence } from 'framer-motion' // 暂时禁用动画
import {
  Search,
  Filter,
  SortAsc,
  SortDesc,
  Clock,
  FileText,
  ExternalLink,
  Star,
  Copy,
  Share2,
  MoreVertical,
  Loader2,
  AlertCircle,
  Sparkles,
  Mic,
  History
} from 'lucide-react'
import { toast } from 'sonner'

import { cn } from '@/utils/cn'
import { useSearch, SearchStrategy, type SearchResultItem } from '@/stores/searchStore'
import SearchMonitoring from '@/components/search/SearchMonitoring'
import ModelSelector from '@/components/search/ModelSelector'
import ModeSelector from '@/components/search/ModeSelector'
import VoiceInput from '@/components/search/VoiceInput'
import SearchHistory from '@/components/search/SearchHistory'

/**
 * 搜索过滤器接口
 */
interface SearchFilters {
  strategy: SearchStrategy
  dateRange: string
  fileType: string
  source: string
  minScore: number
}

/**
 * 搜索页面组件
 * 提供智能搜索功能和结果展示
 */
const SearchPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  
  // 使用搜索store
  const {
    query,
    results,
    loading,
    error,
    totalResults,
    executionTime,
    setQuery,
    performSearch
  } = useSearch()
  
  // UI 状态
  const [showFilters, setShowFilters] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [showVoiceInput, setShowVoiceInput] = useState(false)
  const [sortBy, setSortBy] = useState<'relevance' | 'date' | 'score'>('relevance')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  
  // 搜索配置状态
  const [selectedModel, setSelectedModel] = useState('gpt-4')
  const [selectedMode, setSelectedMode] = useState('semantic')
  
  // 过滤器状态
  const [filters, setFilters] = useState<SearchFilters>({
    strategy: SearchStrategy.SIMILARITY,
    dateRange: 'all',
    fileType: 'all',
    source: 'all',
    minScore: 0,
  })
  
  // 搜索建议
  const [suggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  
  const searchInputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)

  // 初始化搜索
  useEffect(() => {
    const initialQuery = searchParams.get('q')
    if (initialQuery && initialQuery !== query) {
      setQuery(initialQuery)
      performSearch(initialQuery)
    }
  }, [searchParams, query, setQuery, performSearch])

  // 监听查询参数变化
  useEffect(() => {
    const urlQuery = searchParams.get('q')
    if (urlQuery && urlQuery !== query) {
      setQuery(urlQuery)
    }
  }, [searchParams, query, setQuery])

  // 点击外部关闭建议
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        !searchInputRef.current?.contains(event.target as Node)
      ) {
        setShowSuggestions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  /**
   * 处理语音输入转录
   */
  const handleVoiceTranscript = (transcript: string) => {
    setQuery(transcript)
  }

  /**
   * 处理语音输入完成
   */
  const handleVoiceFinalTranscript = (transcript: string) => {
    if (transcript.trim()) {
      setQuery(transcript)
      setSearchParams({ q: transcript.trim() })
      setShowVoiceInput(false)
    }
  }

  /**
   * 处理历史记录项点击
   */
  const handleHistoryItemClick = (item: any) => {
    setQuery(item.query)
    setSearchParams({ q: item.query })
    setShowHistory(false)
  }

  /**
   * 切换语音输入
   */
  const toggleVoiceInput = () => {
    setShowVoiceInput(!showVoiceInput)
  }

  /**
   * 切换历史记录
   */
  const toggleHistory = () => {
    setShowHistory(!showHistory)
  }

  /**
   * 处理搜索提交
   */
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      setSearchParams({ q: query.trim() })
      performSearch(query.trim())
      setShowSuggestions(false)
    }
  }





  /**
   * 选择建议
   */
  const selectSuggestion = (suggestion: string) => {
    setQuery(suggestion)
    setShowSuggestions(false)
    setSearchParams({ q: suggestion })
  }

  /**
   * 复制结果内容
   */
  const copyContent = (content: string) => {
    navigator.clipboard.writeText(content)
    toast.success('内容已复制到剪贴板')
  }

  /**
   * 分享结果
   */
  const shareResult = (result: SearchResultItem) => {
    const shareData = {
      title: result.title || '搜索结果',
      text: result.content.substring(0, 100) + '...',
      url: window.location.href,
    }
    
    if (navigator.share) {
      navigator.share(shareData)
    } else {
      navigator.clipboard.writeText(window.location.href)
      toast.success('链接已复制到剪贴板')
    }
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* 搜索头部 */}
      <div className="mb-8">
        <div className="flex items-center space-x-4 mb-4">
          <h1 className="text-2xl font-bold text-foreground">智能搜索</h1>
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

        {/* 搜索区域 */}
        <div className="bg-card rounded-lg border shadow-sm">
          <form onSubmit={handleSearchSubmit} className="p-6">
            <div className="space-y-4">
              {/* 主搜索输入 */}
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-muted-foreground" />
                </div>
                
                <input
                   ref={searchInputRef}
                   type="text"
                   value={query}
                   onChange={(e) => setQuery(e.target.value)}
                   onFocus={() => query && setShowSuggestions(true)}
                   placeholder="输入您的搜索查询..."
                   className={cn(
                     'block w-full pl-10 pr-20 py-3 text-base',
                     'bg-background border border-input rounded-lg',
                     'placeholder:text-muted-foreground',
                     'focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent',
                     'transition-colors'
                   )}
                 />
                
                <div className="absolute inset-y-0 right-0 flex items-center gap-1 pr-2">
                  {/* 语音输入按钮 */}
                  <button
                    type="button"
                    onClick={toggleVoiceInput}
                    className={cn(
                      'p-2 rounded-md transition-colors',
                      'hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring',
                      showVoiceInput && 'bg-primary text-primary-foreground'
                    )}
                    aria-label="语音输入"
                  >
                    <Mic className="h-4 w-4" />
                  </button>
                  
                  {/* 历史记录按钮 */}
                  <button
                    type="button"
                    onClick={toggleHistory}
                    className={cn(
                      'p-2 rounded-md transition-colors',
                      'hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring',
                      showHistory && 'bg-primary text-primary-foreground'
                    )}
                    aria-label="搜索历史"
                  >
                    <History className="h-4 w-4" />
                  </button>
                  
                  {/* 搜索按钮 */}
                  <button
                    type="submit"
                    disabled={!query.trim() || loading}
                    className={cn(
                      'p-2 rounded-md transition-colors',
                      'hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring',
                      'disabled:opacity-50 disabled:cursor-not-allowed'
                    )}
                  >
                    {loading ? (
                      <Loader2 className="h-5 w-5 animate-spin" />
                    ) : (
                      <Sparkles className="h-5 w-5" />
                    )}
                  </button>
                </div>
              </div>
              
              {/* 语音输入组件 */}
              {showVoiceInput && (
                <div className="overflow-hidden">
                  <VoiceInput
                    onTranscript={handleVoiceTranscript}
                    onFinalTranscript={handleVoiceFinalTranscript}
                    placeholder="开始说话进行搜索..."
                  />
                </div>
              )}
              
              {/* 搜索配置区域 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* 模型选择器 */}
                <div>
                  <label className="block text-sm font-medium mb-2">AI模型</label>
                  <ModelSelector 
                    selectedModel={selectedModel}
                    onModelChange={setSelectedModel}
                  />
                </div>
                
                {/* 检索模式选择器 */}
                <div>
                  <label className="block text-sm font-medium mb-2">检索模式</label>
                  <ModeSelector 
                    selectedMode={selectedMode}
                    onModeChange={setSelectedMode}
                  />
                </div>
              </div>
            </div>
          </form>

          {/* 搜索建议 */}
          {showSuggestions && suggestions.length > 0 && (
            <div
              ref={suggestionsRef}
              className="absolute top-full left-0 right-0 mt-2 bg-popover border rounded-lg shadow-lg z-50"
            >
              <div className="py-2">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => selectSuggestion(suggestion)}
                    className="w-full px-4 py-2 text-left hover:bg-accent flex items-center space-x-2"
                  >
                    <Search className="h-4 w-4 text-muted-foreground" />
                    <span>{suggestion}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 过滤器面板 */}
      {showFilters && (
        <div className="card p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">搜索策略</label>
                <select
                  value={filters.strategy}
                  onChange={(e) => setFilters({ ...filters, strategy: e.target.value as SearchStrategy })}
                  className="input w-full"
                >
                  <option value="similarity">相似度搜索</option>
                  <option value="hybrid">混合搜索</option>
                  <option value="semantic_hybrid">语义混合</option>
                  <option value="keyword">关键词搜索</option>
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
                  <option value="year">本年</option>
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
                  <option value="doc">Word文档</option>
                  <option value="txt">文本文件</option>
                  <option value="md">Markdown</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">最小评分</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={filters.minScore}
                  onChange={(e) => setFilters({ ...filters, minScore: parseFloat(e.target.value) })}
                  className="w-full"
                />
                <div className="text-xs text-muted-foreground mt-1">
                  {(filters.minScore * 100).toFixed(0)}%
                </div>
              </div>
            </div>
        </div>
      )}

      {/* 搜索监控 */}
      <div className="mb-6">
        <SearchMonitoring />
      </div>
    
      {/* 搜索历史记录 */}
      {showHistory && (
        <div className="overflow-hidden mb-6">
          <SearchHistory
            onItemClick={handleHistoryItemClick}
          />
        </div>
      )}

      {/* 搜索结果头部 */}
      {(results.length > 0 || loading || error) && (
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            {!loading && !error && (
              <div className="text-sm text-muted-foreground">
                找到 {totalResults} 个结果 ({executionTime?.toFixed(2) || 0} 秒)
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="input text-sm"
            >
              <option value="relevance">相关度</option>
              <option value="date">日期</option>
              <option value="score">评分</option>
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
          </div>
        </div>
      )}

      {/* 搜索结果 */}
      <div className="space-y-6">
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
              <p className="text-muted-foreground">正在搜索...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <AlertCircle className="h-8 w-8 mx-auto mb-4 text-destructive" />
              <p className="text-destructive mb-4">{error}</p>
              <button
                onClick={() => performSearch(query)}
                className="btn btn-outline btn-sm"
              >
                重试
              </button>
            </div>
          </div>
        )}

        {!loading && !error && results.length === 0 && query && (
          <div className="text-center py-12">
            <Search className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-medium mb-2">未找到相关结果</h3>
            <p className="text-muted-foreground mb-4">
              尝试使用不同的关键词或调整搜索条件
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {['教程', '指南', '最佳实践', '案例研究'].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => selectSuggestion(suggestion)}
                  className="btn btn-outline btn-sm"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {!loading && !error && results.map((result) => (
          <div
            key={result.id}
            className="card p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <h3 className="text-lg font-semibold text-foreground hover:text-primary cursor-pointer">
                    {result.title}
                  </h3>
                  <div className="flex items-center space-x-1">
                    <Star className="h-4 w-4 text-yellow-500" />
                    <span className="text-sm text-muted-foreground">
                      {(result.score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4 text-sm text-muted-foreground mb-3">
                  <span className="flex items-center space-x-1">
                    <FileText className="h-4 w-4" />
                    <span>{result.source}</span>
                  </span>
                  
                  {result.metadata?.date && (
                    <span className="flex items-center space-x-1">
                      <Clock className="h-4 w-4" />
                      <span>{result.metadata.date}</span>
                    </span>
                  )}
                  
                  {result.metadata?.author && (
                    <span>作者: {result.metadata.author}</span>
                  )}
                </div>
              </div>
                
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => copyContent(result.content)}
                  className="btn btn-ghost btn-sm"
                  title="复制内容"
                >
                  <Copy className="h-4 w-4" />
                </button>
                
                <button
                  onClick={() => shareResult(result)}
                  className="btn btn-ghost btn-sm"
                  title="分享"
                >
                  <Share2 className="h-4 w-4" />
                </button>
                
                <button className="btn btn-ghost btn-sm">
                  <MoreVertical className="h-4 w-4" />
                </button>
              </div>
            </div>
              
            <div
              className="text-muted-foreground mb-4 leading-relaxed"
              dangerouslySetInnerHTML={{ __html: result.highlight || result.content }}
            />
            
            {result.metadata?.tags && (
              <div className="flex flex-wrap gap-2 mb-3">
                {result.metadata.tags.map((tag: string, index: number) => (
                  <span
                    key={index}
                    className="badge badge-secondary text-xs"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
            
            {result.url && (
              <div className="flex items-center justify-between">
                <a
                  href={result.url}
                  className="text-primary hover:underline flex items-center space-x-1 text-sm"
                >
                  <span>查看完整文档</span>
                  <ExternalLink className="h-3 w-3" />
                </a>
                
                <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                  <span>排名: #{result.rank}</span>
                  <span>•</span>
                  <span>文档ID: {result.docId}</span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* AI 助手提示 */}
      {!loading && !error && results.length > 0 && (
        <div className="card p-6 mt-8 bg-gradient-to-r from-primary/5 to-secondary/5 border-primary/20">
          <div className="flex items-start space-x-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-foreground mb-2">
                AI 助手建议
              </h3>
              <p className="text-muted-foreground text-sm mb-3">
                基于您的搜索结果，我建议您可以进一步了解相关的最佳实践和高级技巧。
              </p>
              <div className="flex flex-wrap gap-2">
                <button className="btn btn-outline btn-sm">
                  生成摘要
                </button>
                <button className="btn btn-outline btn-sm">
                  相关推荐
                </button>
                <button className="btn btn-outline btn-sm">
                  导出结果
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SearchPage