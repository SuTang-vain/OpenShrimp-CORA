import * as React from 'react'
import { useState } from 'react'
import { ChevronDown, Search, Zap, Brain, Target } from 'lucide-react'
// import { motion, AnimatePresence } from 'framer-motion' // 暂时禁用动画

import { cn } from '@/utils/cn'

/**
 * 检索模式选项接口
 */
export interface ModeOption {
  id: string
  name: string
  description: string
  features: string[]
  icon: React.ReactNode
  color: string
}

/**
 * 模式选择器属性接口
 */
interface ModeSelectorProps {
  selectedMode: string
  onModeChange: (modeId: string) => void
  modes?: ModeOption[]
  disabled?: boolean
  className?: string
}

/**
 * 默认检索模式列表
 */
const defaultModes: ModeOption[] = [
  {
    id: 'semantic',
    name: '语义搜索',
    description: '基于语义理解的智能搜索，理解查询意图',
    features: ['语义理解', '上下文感知', '智能匹配'],
    icon: <Brain className="w-4 h-4" />,
    color: 'blue'
  },
  {
    id: 'hybrid',
    name: '混合搜索',
    description: '结合关键词和语义搜索，提供最佳结果',
    features: ['关键词匹配', '语义理解', '结果融合'],
    icon: <Zap className="w-4 h-4" />,
    color: 'purple'
  },
  {
    id: 'keyword',
    name: '关键词搜索',
    description: '传统的关键词匹配搜索，快速精确',
    features: ['精确匹配', '快速响应', '布尔查询'],
    icon: <Search className="w-4 h-4" />,
    color: 'green'
  },
  {
    id: 'vector',
    name: '向量搜索',
    description: '基于向量相似度的深度搜索',
    features: ['向量匹配', '深度理解', '相似度排序'],
    icon: <Target className="w-4 h-4" />,
    color: 'orange'
  }
]

/**
 * 获取颜色样式
 */
const getColorStyles = (color: string, isSelected: boolean = false) => {
  const colorMap = {
    blue: {
      bg: isSelected ? 'bg-blue-50' : 'bg-white',
      border: isSelected ? 'border-blue-500' : 'border-gray-200',
      text: isSelected ? 'text-blue-700' : 'text-gray-700',
      icon: isSelected ? 'text-blue-500' : 'text-gray-500',
      badge: 'bg-blue-100 text-blue-800'
    },
    purple: {
      bg: isSelected ? 'bg-purple-50' : 'bg-white',
      border: isSelected ? 'border-purple-500' : 'border-gray-200',
      text: isSelected ? 'text-purple-700' : 'text-gray-700',
      icon: isSelected ? 'text-purple-500' : 'text-gray-500',
      badge: 'bg-purple-100 text-purple-800'
    },
    green: {
      bg: isSelected ? 'bg-green-50' : 'bg-white',
      border: isSelected ? 'border-green-500' : 'border-gray-200',
      text: isSelected ? 'text-green-700' : 'text-gray-700',
      icon: isSelected ? 'text-green-500' : 'text-gray-500',
      badge: 'bg-green-100 text-green-800'
    },
    orange: {
      bg: isSelected ? 'bg-orange-50' : 'bg-white',
      border: isSelected ? 'border-orange-500' : 'border-gray-200',
      text: isSelected ? 'text-orange-700' : 'text-gray-700',
      icon: isSelected ? 'text-orange-500' : 'text-gray-500',
      badge: 'bg-orange-100 text-orange-800'
    }
  }
  
  return colorMap[color as keyof typeof colorMap] || colorMap.blue
}

/**
 * 模式选择器组件
 * 提供检索模式选择功能
 */
const ModeSelector: React.FC<ModeSelectorProps> = ({
  selectedMode,
  onModeChange,
  modes = defaultModes,
  disabled = false,
  className
}) => {
  const [isOpen, setIsOpen] = useState(false)
  
  // 获取当前选中的模式
  const currentMode = modes.find(mode => mode.id === selectedMode) || modes[0]
  const currentStyles = getColorStyles(currentMode.color, true)
  
  /**
   * 处理模式选择
   */
  const handleModeSelect = (modeId: string) => {
    onModeChange(modeId)
    setIsOpen(false)
  }
  
  /**
   * 切换下拉菜单
   */
  const toggleDropdown = () => {
    if (!disabled) {
      setIsOpen(!isOpen)
    }
  }
  
  return (
    <div className={cn('relative', className)}>
      {/* 选择器按钮 */}
      <button
        type="button"
        onClick={toggleDropdown}
        disabled={disabled}
        className={cn(
          'flex items-center justify-between w-full px-4 py-2.5',
          'border rounded-lg shadow-sm',
          'hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-opacity-20',
          'transition-all duration-200',
          currentStyles.bg,
          currentStyles.border,
          disabled && 'opacity-50 cursor-not-allowed',
          isOpen && 'ring-2',
          currentMode.color === 'blue' && isOpen && 'ring-blue-500',
          currentMode.color === 'purple' && isOpen && 'ring-purple-500',
          currentMode.color === 'green' && isOpen && 'ring-green-500',
          currentMode.color === 'orange' && isOpen && 'ring-orange-500'
        )}
      >
        <div className="flex items-center space-x-3">
          {/* 模式图标 */}
          <div className={cn('flex-shrink-0', currentStyles.icon)}>
            {currentMode.icon}
          </div>
          
          {/* 模式信息 */}
          <div className="flex flex-col items-start">
            <span className={cn('text-sm font-medium', currentStyles.text)}>
              {currentMode.name}
            </span>
            <span className="text-xs text-gray-500">
              {currentMode.features[0]}
            </span>
          </div>
        </div>
        
        {/* 下拉箭头 */}
        <ChevronDown
          className={cn(
            'w-4 h-4 text-gray-400 transition-transform duration-200',
            isOpen && 'transform rotate-180'
          )}
        />
      </button>
      
      {/* 下拉菜单 */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 z-50">
            <div className="bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden">
              <div className="py-1">
                {modes.map((mode) => {
                  const isSelected = selectedMode === mode.id
                  const modeStyles = getColorStyles(mode.color, isSelected)
                  
                  return (
                    <button
                      key={mode.id}
                      type="button"
                      onClick={() => handleModeSelect(mode.id)}
                      className={cn(
                        'w-full px-4 py-3 text-left hover:bg-gray-50',
                        'transition-colors duration-150',
                        'focus:outline-none focus:bg-gray-50',
                        isSelected && modeStyles.bg,
                        isSelected && 'border-r-2',
                        isSelected && modeStyles.border
                      )}
                    >
                      <div className="flex items-start space-x-3">
                        {/* 模式图标 */}
                        <div className={cn('flex-shrink-0 mt-0.5', modeStyles.icon)}>
                          {mode.icon}
                        </div>
                        
                        {/* 模式详细信息 */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <span className={cn('text-sm font-medium', modeStyles.text)}>
                              {mode.name}
                            </span>
                          </div>
                          
                          <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                            {mode.description}
                          </p>
                          
                          {/* 特性标签 */}
                          <div className="flex flex-wrap gap-1 mt-2">
                            {mode.features.slice(0, 3).map((feature) => (
                              <span
                                key={feature}
                                className={cn(
                                  'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                                  isSelected ? modeStyles.badge : 'bg-gray-100 text-gray-800'
                                )}
                              >
                                {feature}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </button>
                  )
                })}
              </div>
              
              {/* 底部提示 */}
              <div className="px-4 py-2 bg-gray-50 border-t border-gray-100">
                <p className="text-xs text-gray-500">
                  选择适合的检索模式以获得最佳搜索结果
                </p>
              </div>
            </div>
        </div>
      )}
      
      {/* 点击外部关闭 */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  )
}

export default ModeSelector
export type { ModeSelectorProps }