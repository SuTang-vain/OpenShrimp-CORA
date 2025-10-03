import * as React from 'react'
import { useState } from 'react'
import { ChevronDown, Brain, Zap, Settings } from 'lucide-react'
// import { motion, AnimatePresence } from 'framer-motion' // 暂时禁用动画

import { cn } from '@/utils/cn'
import { useConfigStore } from '@/stores/configStore'
import { ServiceType, ServiceStatus, LLMServiceConfig } from '@/types/services'

/**
 * AI模型选项接口
 */
export interface ModelOption {
  id: string
  name: string
  description: string
  provider: string
  capabilities: string[]
  isAvailable: boolean
  status?: ServiceStatus
  icon?: React.ReactNode
}

/**
 * 模型选择器属性接口
 */
interface ModelSelectorProps {
  selectedModel: string
  onModelChange: (modelId: string) => void
  models?: ModelOption[]
  disabled?: boolean
  className?: string
}

/**
 * 默认模型列表
 */
const defaultModels: ModelOption[] = [
  {
    id: 'gpt-4',
    name: 'GPT-4',
    description: '最先进的语言模型，适合复杂推理和分析',
    provider: 'OpenAI',
    capabilities: ['文本生成', '代码分析', '复杂推理'],
    isAvailable: true,
    status: ServiceStatus.CONNECTED,
    icon: <Brain className="w-4 h-4" />
  },
  {
    id: 'gpt-3.5-turbo',
    name: 'GPT-3.5 Turbo',
    description: '快速响应的语言模型，适合一般查询',
    provider: 'OpenAI',
    capabilities: ['文本生成', '快速响应'],
    isAvailable: true,
    status: ServiceStatus.CONNECTED,
    icon: <Zap className="w-4 h-4" />
  },
  {
    id: 'claude-3',
    name: 'Claude 3',
    description: 'Anthropic的先进模型，擅长分析和推理',
    provider: 'Anthropic',
    capabilities: ['深度分析', '安全对话'],
    isAvailable: true,
    status: ServiceStatus.CONNECTED,
    icon: <Settings className="w-4 h-4" />
  },
  {
    id: 'gemini-pro',
    name: 'Gemini Pro',
    description: 'Google的多模态模型，支持文本和图像',
    provider: 'Google',
    capabilities: ['多模态', '文本生成'],
    isAvailable: true,
    status: ServiceStatus.DISCONNECTED,
    icon: <Brain className="w-4 h-4" />
  }
]

/**
 * 获取状态徽标显示
 */
const getStatusBadge = (status?: ServiceStatus) => {
  switch (status) {
    case ServiceStatus.CONNECTED:
      return { label: '已连接', cls: 'text-green-600 bg-green-100' }
    case ServiceStatus.TESTING:
      return { label: '测试中', cls: 'text-blue-600 bg-blue-100' }
    case ServiceStatus.ERROR:
      return { label: '连接失败', cls: 'text-red-600 bg-red-100' }
    case ServiceStatus.DISCONNECTED:
      return { label: '未测试', cls: 'text-gray-600 bg-gray-100' }
    default:
      return { label: '未知', cls: 'text-gray-600 bg-gray-100' }
  }
}

/**
 * 模型选择器组件
 * 提供AI模型选择功能
 */
const ModelSelector: React.FC<ModelSelectorProps> = ({
  selectedModel,
  onModelChange,
  models = defaultModels,
  disabled = false,
  className
}) => {
  const [isOpen, setIsOpen] = useState(false)
  // 从配置 store 获取服务列表
  const services = useConfigStore((state) => state.services)

  // 已启用的 LLM 服务（不区分连接状态）
  const enabledLLMServices = React.useMemo(
    () =>
      services.filter((s) => s.type === ServiceType.LLM && s.enabled) as LLMServiceConfig[],
    [services]
  )

  // 将服务映射为模型选项
  const storeModels: ModelOption[] = React.useMemo(
    () =>
      enabledLLMServices.map((s) => ({
        id: s.model ?? s.id,
        name: s.model ?? s.name,
        description: s.description ?? '已配置的模型服务',
        provider: s.name,
        capabilities: ['文本生成'],
        // 允许选择，但用状态徽标区分
        isAvailable: true,
        status: s.status,
        icon: <Brain className="w-4 h-4" />
      })),
    [enabledLLMServices]
  )

  // 实际使用的模型列表（优先使用 store 中的）
  const effectiveModels = storeModels.length > 0 ? storeModels : models
  
  // 当前选中模型
  const currentModel =
    effectiveModels.find((model) => model.id === selectedModel) || effectiveModels[0]
  
  // 列表展示的模型（不再按isAvailable过滤，全部展示）
  const listedModels = effectiveModels
  
  /**
   * 处理模型选择
   */
  const handleModelSelect = (modelId: string) => {
    onModelChange(modelId)
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
          'bg-white border border-gray-200 rounded-lg shadow-sm',
          'hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
          'transition-all duration-200',
          disabled && 'opacity-50 cursor-not-allowed',
          isOpen && 'border-blue-500 ring-2 ring-blue-500 ring-opacity-20'
        )}
      >
        <div className="flex items-center space-x-3">
          {/* 模型图标 */}
          <div className="flex-shrink-0 text-gray-500">{currentModel?.icon}</div>
          
          {/* 模型信息 */}
          <div className="flex flex-col items-start">
            <span className="text-sm font-medium text-gray-900">{currentModel?.name}</span>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">{currentModel?.provider}</span>
              {/* 状态徽标 */}
              {(() => {
                const badge = getStatusBadge(currentModel?.status)
                return (
                  <span className={cn('text-xs px-1.5 py-0.5 rounded', badge.cls)}>{badge.label}</span>
                )
              })()}
            </div>
          </div>
        </div>
        
        {/* 下拉箭头 */}
        <ChevronDown
          className={cn('w-4 h-4 text-gray-400 transition-transform duration-200', isOpen && 'transform rotate-180')}
        />
      </button>
      
      {/* 下拉菜单 */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 z-50">
          <div className="bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden">
            <div className="py-1">
              {listedModels.map((model) => {
                const badge = getStatusBadge(model.status)
                return (
                  <button
                    key={model.id}
                    type="button"
                    onClick={() => handleModelSelect(model.id)}
                    className={cn(
                      'w-full px-4 py-3 text-left hover:bg-gray-50',
                      'transition-colors duration-150',
                      'focus:outline-none focus:bg-gray-50',
                      selectedModel === model.id && 'bg-blue-50 border-r-2 border-blue-500'
                    )}
                  >
                    <div className="flex items-start space-x-3">
                      {/* 模型图标 */}
                      <div className="flex-shrink-0 mt-0.5 text-gray-500">{model.icon}</div>
                      
                      {/* 模型详细信息 */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-900">{model.name}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-500">{model.provider}</span>
                            <span className={cn('text-xs px-1.5 py-0.5 rounded', badge.cls)}>{badge.label}</span>
                          </div>
                        </div>
                        
                        <p className="text-xs text-gray-600 mt-1 line-clamp-2">{model.description}</p>
                        
                        {/* 能力标签 */}
                        <div className="flex flex-wrap gap-1 mt-2">
                          {model.capabilities.slice(0, 2).map((capability) => (
                            <span key={capability} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                              {capability}
                            </span>
                          ))}
                          {model.capabilities.length > 2 && (
                            <span className="text-xs text-gray-500">+{model.capabilities.length - 2} 更多</span>
                          )}
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
                {storeModels.length > 0
                  ? '提示：未测试或失败的服务可在服务配置页执行“测试连接”或检查密钥与地址。'
                  : '未检测到已配置的AI模型服务，请前往服务管理页面进行配置'}
              </p>
            </div>
          </div>
        </div>
      )}
      
      {/* 点击外部关闭 */}
      {isOpen && <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />}
    </div>
  )
}

export default ModelSelector
export type { ModelSelectorProps }