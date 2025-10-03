import * as React from 'react'
import { useState, useEffect } from 'react'
// import { motion, AnimatePresence } from 'framer-motion'
import {
  Activity,
  CheckCircle,
  AlertCircle,
  Loader2,
  Search,
  Database,
  Brain,
  TrendingUp,
  X
} from 'lucide-react'

import { cn } from '@/utils/cn'

/**
 * 搜索阶段枚举
 */
export enum SearchPhase {
  IDLE = 'idle',
  QUERY_ANALYSIS = 'query_analysis',
  RETRIEVAL = 'retrieval',
  RERANKING = 'reranking',
  GENERATION = 'generation',
  COMPLETED = 'completed',
  ERROR = 'error'
}

/**
 * 搜索步骤接口
 */
export interface SearchStep {
  id: string
  name: string
  description: string
  phase: SearchPhase
  status: 'pending' | 'running' | 'completed' | 'error'
  startTime?: number
  endTime?: number
  progress?: number
  metadata?: Record<string, any>
}

/**
 * 搜索监控数据接口
 */
export interface SearchMonitoringData {
  searchId: string
  query: string
  status: 'running' | 'completed' | 'error'
  currentPhase: SearchPhase
  steps: SearchStep[]
  totalTime?: number
  metrics?: {
    documentsRetrieved: number
    tokensGenerated: number
    confidence: number
  }
}

/**
 * 搜索监控组件属性接口
 */
interface SearchMonitoringProps {
  data?: SearchMonitoringData
  isVisible?: boolean
  onClose?: () => void
  className?: string
}

/**
 * 默认搜索步骤
 */
const defaultSteps: SearchStep[] = [
  {
    id: 'query_analysis',
    name: '查询分析',
    description: '分析查询意图和关键词',
    phase: SearchPhase.QUERY_ANALYSIS,
    status: 'pending'
  },
  {
    id: 'retrieval',
    name: '文档检索',
    description: '从知识库中检索相关文档',
    phase: SearchPhase.RETRIEVAL,
    status: 'pending'
  },
  {
    id: 'reranking',
    name: '结果重排',
    description: '对检索结果进行相关性重排',
    phase: SearchPhase.RERANKING,
    status: 'pending'
  },
  {
    id: 'generation',
    name: '答案生成',
    description: '基于检索内容生成智能回答',
    phase: SearchPhase.GENERATION,
    status: 'pending'
  }
]

/**
 * 获取阶段图标
 */
const getPhaseIcon = (phase: SearchPhase, status: string) => {
  const iconClass = 'w-4 h-4'
  
  if (status === 'running') {
    return <Loader2 className={cn(iconClass, 'animate-spin text-blue-500')} />
  }
  
  if (status === 'completed') {
    return <CheckCircle className={cn(iconClass, 'text-green-500')} />
  }
  
  if (status === 'error') {
    return <AlertCircle className={cn(iconClass, 'text-red-500')} />
  }
  
  switch (phase) {
    case SearchPhase.QUERY_ANALYSIS:
      return <Search className={cn(iconClass, 'text-gray-400')} />
    case SearchPhase.RETRIEVAL:
      return <Database className={cn(iconClass, 'text-gray-400')} />
    case SearchPhase.RERANKING:
      return <TrendingUp className={cn(iconClass, 'text-gray-400')} />
    case SearchPhase.GENERATION:
      return <Brain className={cn(iconClass, 'text-gray-400')} />
    default:
      return <Activity className={cn(iconClass, 'text-gray-400')} />
  }
}

/**
 * 格式化时间
 */
const formatTime = (ms: number): string => {
  if (ms < 1000) {
    return `${ms}ms`
  }
  return `${(ms / 1000).toFixed(1)}s`
}

/**
 * 搜索监控组件
 * 显示搜索过程的实时进度和状态
 */
const SearchMonitoring: React.FC<SearchMonitoringProps> = ({
  data,
  isVisible = true,
  onClose,
  className
}) => {
  const [currentTime, setCurrentTime] = useState(Date.now())
  
  // 更新当前时间（用于计算运行时间）
  useEffect(() => {
    if (!data || data.status !== 'running') return
    
    const interval = setInterval(() => {
      setCurrentTime(Date.now())
    }, 100)
    
    return () => clearInterval(interval)
  }, [data])
  
  // 如果没有数据或不可见，不渲染
  if (!isVisible || !data) {
    return null
  }
  
  const steps = data.steps.length > 0 ? data.steps : defaultSteps
  const completedSteps = steps.filter(step => step.status === 'completed').length
  const totalSteps = steps.length
  const overallProgress = (completedSteps / totalSteps) * 100
  
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 20 }}
        className={cn(
          'bg-white border border-gray-200 rounded-lg shadow-lg',
          'max-w-md w-full',
          className
        )}
      >
        {/* 头部 */}
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <div className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-blue-500" />
            <h3 className="text-sm font-semibold text-gray-900">
              搜索监控
            </h3>
          </div>
          
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-100 rounded-md transition-colors"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          )}
        </div>
        
        {/* 查询信息 */}
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-500">查询</span>
            <span className="text-xs text-gray-400">
              ID: {data.searchId.slice(-8)}
            </span>
          </div>
          <p className="text-sm text-gray-900 truncate" title={data.query}>
            {data.query}
          </p>
        </div>
        
        {/* 总体进度 */}
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-500">总体进度</span>
            <span className="text-xs text-gray-600">
              {completedSteps}/{totalSteps} 步骤
            </span>
          </div>
          
          <div className="w-full bg-gray-200 rounded-full h-2">
            <motion.div
              className="bg-blue-500 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${overallProgress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
          
          <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
            <span>{Math.round(overallProgress)}% 完成</span>
            {data.totalTime && (
              <span>耗时 {formatTime(data.totalTime)}</span>
            )}
          </div>
        </div>
        
        {/* 步骤列表 */}
        <div className="p-4">
          <div className="space-y-3">
            {steps.map((step, index) => {
              const isActive = step.status === 'running'
              const isCompleted = step.status === 'completed'
              const isError = step.status === 'error'
              const duration = step.startTime && step.endTime 
                ? step.endTime - step.startTime 
                : step.startTime && isActive 
                  ? currentTime - step.startTime 
                  : undefined
              
              return (
                <motion.div
                  key={step.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={cn(
                    'flex items-start space-x-3 p-3 rounded-lg transition-colors',
                    isActive && 'bg-blue-50 border border-blue-200',
                    isCompleted && 'bg-green-50',
                    isError && 'bg-red-50'
                  )}
                >
                  {/* 步骤图标 */}
                  <div className="flex-shrink-0 mt-0.5">
                    {getPhaseIcon(step.phase, step.status)}
                  </div>
                  
                  {/* 步骤信息 */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h4 className={cn(
                        'text-sm font-medium',
                        isActive && 'text-blue-700',
                        isCompleted && 'text-green-700',
                        isError && 'text-red-700',
                        step.status === 'pending' && 'text-gray-500'
                      )}>
                        {step.name}
                      </h4>
                      
                      {duration && (
                        <span className="text-xs text-gray-500">
                          {formatTime(duration)}
                        </span>
                      )}
                    </div>
                    
                    <p className="text-xs text-gray-600 mt-1">
                      {step.description}
                    </p>
                    
                    {/* 步骤进度条 */}
                    {isActive && step.progress !== undefined && (
                      <div className="mt-2">
                        <div className="w-full bg-blue-200 rounded-full h-1">
                          <motion.div
                            className="bg-blue-500 h-1 rounded-full"
                            initial={{ width: 0 }}
                            animate={{ width: `${step.progress}%` }}
                            transition={{ duration: 0.3 }}
                          />
                        </div>
                      </div>
                    )}
                    
                    {/* 步骤元数据 */}
                    {step.metadata && Object.keys(step.metadata).length > 0 && (
                      <div className="mt-2 text-xs text-gray-500">
                        {Object.entries(step.metadata).map(([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span>{key}:</span>
                            <span>{String(value)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </motion.div>
              )
            })}
          </div>
        </div>
        
        {/* 指标信息 */}
        {data.metrics && (
          <div className="p-4 border-t border-gray-100 bg-gray-50">
            <h4 className="text-xs font-medium text-gray-500 mb-2">搜索指标</h4>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-lg font-semibold text-gray-900">
                  {data.metrics.documentsRetrieved}
                </div>
                <div className="text-xs text-gray-500">检索文档</div>
              </div>
              
              <div>
                <div className="text-lg font-semibold text-gray-900">
                  {data.metrics.tokensGenerated}
                </div>
                <div className="text-xs text-gray-500">生成Token</div>
              </div>
              
              <div>
                <div className="text-lg font-semibold text-gray-900">
                  {Math.round(data.metrics.confidence * 100)}%
                </div>
                <div className="text-xs text-gray-500">置信度</div>
              </div>
            </div>
          </div>
        )}
        
        {/* 状态指示器 */}
        <div className={cn(
          'px-4 py-2 text-center text-xs font-medium',
          data.status === 'running' && 'bg-blue-100 text-blue-700',
          data.status === 'completed' && 'bg-green-100 text-green-700',
          data.status === 'error' && 'bg-red-100 text-red-700'
        )}>
          {data.status === 'running' && (
            <div className="flex items-center justify-center space-x-1">
              <Loader2 className="w-3 h-3 animate-spin" />
              <span>搜索进行中...</span>
            </div>
          )}
          {data.status === 'completed' && (
            <div className="flex items-center justify-center space-x-1">
              <CheckCircle className="w-3 h-3" />
              <span>搜索完成</span>
            </div>
          )}
          {data.status === 'error' && (
            <div className="flex items-center justify-center space-x-1">
              <AlertCircle className="w-3 h-3" />
              <span>搜索失败</span>
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  )
}

export default SearchMonitoring
export type { SearchMonitoringProps }