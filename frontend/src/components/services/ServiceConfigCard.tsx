import * as React from 'react'
import { useState } from 'react'
import {
  ChevronDown,
  ChevronUp,
  Eye,
  EyeOff,
  ExternalLink,
  Settings,
  TestTube,
  Trash2,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
} from 'lucide-react'
import { cn } from '@/utils/cn'
import { 
  ServiceConfig, 
  ServiceTemplate, 
  ServiceStatus, 
  ServiceType,
  ServiceConfigFormData 
} from '@/types/services'
import { useConfigStore } from '@/stores/configStore'

/**
 * 服务配置卡片组件属性
 */
interface ServiceConfigCardProps {
  template: ServiceTemplate
  config?: ServiceConfig
  onSave?: (config: ServiceConfig) => void
  onDelete?: (id: string) => void
  className?: string
}

/**
 * 获取状态图标和颜色
 */
const getStatusDisplay = (status: ServiceStatus) => {
  switch (status) {
    case ServiceStatus.CONNECTED:
      return {
        icon: CheckCircle,
        color: 'text-green-500',
        bgColor: 'bg-green-50',
        label: '已连接'
      }
    case ServiceStatus.DISCONNECTED:
      return {
        icon: XCircle,
        color: 'text-gray-500',
        bgColor: 'bg-gray-50',
        label: '未连接'
      }
    case ServiceStatus.TESTING:
      return {
        icon: Clock,
        color: 'text-blue-500',
        bgColor: 'bg-blue-50',
        label: '测试中'
      }
    case ServiceStatus.ERROR:
      return {
        icon: AlertCircle,
        color: 'text-red-500',
        bgColor: 'bg-red-50',
        label: '连接失败'
      }
    default:
      return {
        icon: XCircle,
        color: 'text-gray-500',
        bgColor: 'bg-gray-50',
        label: '未知状态'
      }
  }
}

/**
 * 服务配置卡片组件
 */
const ServiceConfigCard: React.FC<ServiceConfigCardProps> = ({
  template,
  config,
  onSave,
  onDelete,
  className
}) => {
  const { testService, updateService, removeService } = useConfigStore()
  
  // 状态管理
  const [isExpanded, setIsExpanded] = useState(false)
  const [isEditing, setIsEditing] = useState(!config)
  const [showApiKey, setShowApiKey] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  
  // 表单数据
  const [formData, setFormData] = useState<ServiceConfigFormData>(() => {
    if (config) {
      return {
        name: config.name,
        description: config.description,
        enabled: config.enabled,
        ...(config.type === ServiceType.LLM && {
          apiKey: (config as any).apiKey || '',
          baseUrl: (config as any).baseUrl || '',
          model: (config as any).model || '',
          maxTokens: (config as any).maxTokens || 2000,
          temperature: (config as any).temperature || 0.7
        }),
        ...(config.type === ServiceType.WEB_CRAWLER && {
          apiKey: (config as any).apiKey || '',
          baseUrl: (config as any).baseUrl || '',
          maxPages: (config as any).maxPages || 10,
          timeout: (config as any).timeout || 30000
        }),
        ...(config.type === ServiceType.KNOWLEDGE_GRAPH && {
          connectionUrl: (config as any).connectionUrl || '',
          username: (config as any).username || '',
          password: (config as any).password || '',
          authType: (config as any).authType || 'basic',
          database: (config as any).database || '',
          apiKey: (config as any).apiKey || ''
        }),
        ...(config.type === ServiceType.LOCAL_MODEL && {
          baseUrl: (config as any).baseUrl || '',
          healthCheckUrl: (config as any).healthCheckUrl || '',
          apiKey: (config as any).apiKey || ''
        })
      }
    }
    return {
      name: template.name,
      description: template.description,
      enabled: true,
      ...template.defaultConfig
    }
  })

  // 状态显示
  const statusDisplay = config ? getStatusDisplay(config.status) : null
  const StatusIcon = statusDisplay?.icon

  /**
   * 处理表单提交
   */
  const handleSave = () => {
    const baseConfig = {
      id: config?.id || `${template.id}-${Date.now()}`,
      name: formData.name,
      type: template.type,
      description: formData.description,
      officialUrl: template.officialUrl,
      enabled: formData.enabled,
      status: config?.status || ServiceStatus.DISCONNECTED,
      lastTested: config?.lastTested,
      errorMessage: config?.errorMessage
    }

    let serviceConfig: ServiceConfig

    switch (template.type) {
      case ServiceType.LLM:
        serviceConfig = {
          ...baseConfig,
          type: ServiceType.LLM,
          apiKey: formData.apiKey || '',
          baseUrl: formData.baseUrl,
          model: formData.model,
          maxTokens: formData.maxTokens,
          temperature: formData.temperature
        } as ServiceConfig
        break

      case ServiceType.WEB_CRAWLER:
        serviceConfig = {
          ...baseConfig,
          type: ServiceType.WEB_CRAWLER,
          apiKey: formData.apiKey || '',
          baseUrl: formData.baseUrl,
          maxPages: formData.maxPages,
          timeout: formData.timeout
        } as ServiceConfig
        break

      case ServiceType.KNOWLEDGE_GRAPH:
        serviceConfig = {
          ...baseConfig,
          type: ServiceType.KNOWLEDGE_GRAPH,
          connectionUrl: formData.connectionUrl || '',
          username: formData.username,
          password: formData.password,
          authType: formData.authType || 'basic',
          database: formData.database,
          apiKey: formData.apiKey
        } as ServiceConfig
        break

      case ServiceType.LOCAL_MODEL:
        serviceConfig = {
          ...baseConfig,
          type: ServiceType.LOCAL_MODEL,
          baseUrl: formData.baseUrl || '',
          healthCheckUrl: formData.healthCheckUrl,
          apiKey: formData.apiKey
        } as ServiceConfig
        break

      default:
        return
    }

    if (config) {
      updateService(config.id, serviceConfig)
    } else {
      onSave?.(serviceConfig)
    }
    
    setIsEditing(false)
  }

  /**
   * 处理测试连接
   */
  const handleTest = async () => {
    if (!config) return
    
    setIsTesting(true)
    try {
      await testService(config.id)
    } finally {
      setIsTesting(false)
    }
  }

  /**
   * 处理删除
   */
  const handleDelete = () => {
    if (config) {
      removeService(config.id)
      onDelete?.(config.id)
    }
    setShowDeleteDialog(false)
  }

  /**
   * 渲染表单字段
   */
  const renderFormFields = () => {
    const fields = []

    // 基础字段
    fields.push(
      <div key="name" className="space-y-2">
        <label htmlFor={`${template.id}-name`} className="text-sm font-medium">服务名称</label>
        <input
          id={`${template.id}-name`}
          className="input"
          value={formData.name}
          onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
          placeholder="输入服务名称"
        />
      </div>
    )

    fields.push(
      <div key="description" className="space-y-2">
        <label htmlFor={`${template.id}-description`} className="text-sm font-medium">描述</label>
        <textarea
          id={`${template.id}-description`}
          className="input min-h-[80px] resize-none"
          value={formData.description}
          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
          placeholder="输入服务描述"
          rows={2}
        />
      </div>
    )

    // API Key字段（大部分服务都需要）
    if (template.requiredFields.includes('apiKey') || template.optionalFields.includes('apiKey')) {
      fields.push(
        <div key="apiKey" className="space-y-2">
          <label htmlFor={`${template.id}-apiKey`} className="text-sm font-medium">
            API Key {template.requiredFields.includes('apiKey') && <span className="text-red-500">*</span>}
          </label>
          <div className="relative">
            <input
              id={`${template.id}-apiKey`}
              type={showApiKey ? 'text' : 'password'}
              className="input pr-10"
              value={formData.apiKey || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, apiKey: e.target.value }))}
              placeholder="输入API Key"
            />
            <button
              type="button"
              className="absolute right-0 top-0 h-full px-3 btn btn-ghost"
              onClick={() => setShowApiKey(!showApiKey)}
            >
              {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>
      )
    }

    // 根据服务类型添加特定字段
    switch (template.type) {
      case ServiceType.LLM:
        fields.push(
          <div key="baseUrl" className="space-y-2">
            <label htmlFor={`${template.id}-baseUrl`} className="text-sm font-medium">Base URL</label>
            <input
              id={`${template.id}-baseUrl`}
              className="input"
              value={formData.baseUrl || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, baseUrl: e.target.value }))}
              placeholder="输入API Base URL"
            />
          </div>,
          <div key="model" className="space-y-2">
            <label htmlFor={`${template.id}-model`} className="text-sm font-medium">模型</label>
            <input
              id={`${template.id}-model`}
              className="input"
              value={formData.model || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, model: e.target.value }))}
              placeholder="输入模型名称"
            />
          </div>
        )
        break

      case ServiceType.WEB_CRAWLER:
        fields.push(
          <div key="baseUrl" className="space-y-2">
            <label htmlFor={`${template.id}-baseUrl`} className="text-sm font-medium">Base URL</label>
            <input
              id={`${template.id}-baseUrl`}
              className="input"
              value={formData.baseUrl || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, baseUrl: e.target.value }))}
              placeholder="输入API Base URL"
            />
          </div>
        )
        break

      case ServiceType.KNOWLEDGE_GRAPH:
        fields.push(
          <div key="connectionUrl" className="space-y-2">
            <label htmlFor={`${template.id}-connectionUrl`} className="text-sm font-medium">
              连接URL <span className="text-red-500">*</span>
            </label>
            <input
              id={`${template.id}-connectionUrl`}
              className="input"
              value={formData.connectionUrl || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, connectionUrl: e.target.value }))}
              placeholder="bolt://localhost:7687"
            />
          </div>,
          <div key="username" className="space-y-2">
            <label htmlFor={`${template.id}-username`} className="text-sm font-medium">用户名</label>
            <input
              id={`${template.id}-username`}
              className="input"
              value={formData.username || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
              placeholder="输入用户名"
            />
          </div>,
          <div key="password" className="space-y-2">
            <label htmlFor={`${template.id}-password`} className="text-sm font-medium">密码</label>
            <div className="relative">
              <input
                id={`${template.id}-password`}
                type={showPassword ? 'text' : 'password'}
                className="input pr-10"
                value={formData.password || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                placeholder="输入密码"
              />
              <button
                type="button"
                className="absolute right-0 top-0 h-full px-3 btn btn-ghost"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>
        )
        break

      case ServiceType.LOCAL_MODEL:
        fields.push(
          <div key="baseUrl" className="space-y-2">
            <label htmlFor={`${template.id}-baseUrl`} className="text-sm font-medium">
              服务地址 <span className="text-red-500">*</span>
            </label>
            <input
              id={`${template.id}-baseUrl`}
              className="input"
              value={formData.baseUrl || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, baseUrl: e.target.value }))}
              placeholder="http://localhost:11434"
            />
          </div>
        )
        break
    }

    return fields
  }

  return (
    <div className={cn('card w-full', className)}>
      <div className="card-header">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="text-2xl">{template.icon}</div>
            <div>
              <h3 className="card-title text-lg flex items-center space-x-2">
                <span>{config?.name || template.name}</span>
                {config && StatusIcon && (
                  <div className={cn('flex items-center space-x-1', statusDisplay.color)}>
                    <StatusIcon className="h-4 w-4" />
                    <span className="text-xs">{statusDisplay.label}</span>
                  </div>
                )}
              </h3>
              <p className="card-description">{config?.description || template.description}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {config && (
              <>
                <div className="flex items-center space-x-2">
                  <label htmlFor={`${config.id}-enabled`} className="text-sm">启用</label>
                  <input
                    id={`${config.id}-enabled`}
                    type="checkbox"
                    checked={config.enabled}
                    onChange={(e) => updateService(config.id, { enabled: e.target.checked })}
                    className="w-4 h-4"
                  />
                </div>
                
                <button
                  className="btn btn-outline btn-sm"
                  onClick={handleTest}
                  disabled={isTesting || config.status === ServiceStatus.TESTING}
                >
                  <TestTube className="h-4 w-4 mr-1" />
                  {isTesting ? '测试中...' : '测试连接'}
                </button>
              </>
            )}
            
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
          </div>
        </div>
        
        {/* 标签 */}
        {template.tags && template.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {template.tags.map(tag => (
              <span key={tag} className="badge badge-secondary text-xs">
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {isExpanded && (
        <div className="card-content space-y-6">
          {/* 官方链接和操作指引 */}
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-medium mb-2">官方网站</h4>
              <a
                href={template.officialUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-outline btn-sm"
              >
                <ExternalLink className="h-4 w-4 mr-1" />
                访问官网
              </a>
            </div>
            
            <div>
              <h4 className="text-sm font-medium mb-2">配置步骤</h4>
              <ol className="text-sm text-muted-foreground space-y-1">
                {template.setupInstructions.map((instruction, index) => (
                  <li key={index} className="flex">
                    <span className="mr-2">{index + 1}.</span>
                    <span>{instruction}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>

          {/* 配置表单 */}
          {isEditing ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium">服务配置</h4>
                <div className="flex space-x-2">
                  <button
                    className="btn btn-outline btn-sm"
                    onClick={() => setIsEditing(false)}
                  >
                    取消
                  </button>
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={handleSave}
                  >
                    保存
                  </button>
                </div>
              </div>
              
              <div className="grid gap-4">
                {renderFormFields()}
              </div>
            </div>
          ) : config ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium">服务信息</h4>
                <div className="flex space-x-2">
                  <button
                    className="btn btn-outline btn-sm"
                    onClick={() => setIsEditing(true)}
                  >
                    <Settings className="h-4 w-4 mr-1" />
                    编辑
                  </button>
                  
                  <button
                    className="btn btn-outline btn-sm"
                    onClick={() => setShowDeleteDialog(true)}
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    删除
                  </button>
                </div>
              </div>
              
              {/* 显示配置信息 */}
              <div className="grid gap-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">状态:</span>
                  <span className={statusDisplay?.color}>{statusDisplay?.label}</span>
                </div>
                {config.lastTested && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">最后测试:</span>
                    <span>{config.lastTested.toLocaleString()}</span>
                  </div>
                )}
                {config.errorMessage && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">错误信息:</span>
                    <span className="text-red-500 text-xs">{config.errorMessage}</span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="text-center py-4">
              <button
                className="btn btn-primary"
                onClick={() => setIsEditing(true)}
              >
                配置服务
              </button>
            </div>
          )}
        </div>
      )}

      {/* 删除确认对话框 */}
      {showDeleteDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-2">确认删除</h3>
            <p className="text-muted-foreground mb-4">
              确定要删除服务配置 "{config?.name}" 吗？此操作无法撤销。
            </p>
            <div className="flex justify-end space-x-2">
              <button
                className="btn btn-outline"
                onClick={() => setShowDeleteDialog(false)}
              >
                取消
              </button>
              <button
                className="btn btn-destructive"
                onClick={handleDelete}
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ServiceConfigCard