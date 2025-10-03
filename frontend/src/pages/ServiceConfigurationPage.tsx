import * as React from 'react'
import { useState, useMemo } from 'react'
import { Helmet } from 'react-helmet-async'
import {
  Settings,
  Plus,
  Download,
  Upload,
  RotateCcw,
  Filter,
  Search,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Zap,
  Globe,
  Database,
  Server,
} from 'lucide-react'
import { cn } from '@/utils/cn'
import { ServiceType, ServiceStatus } from '@/types/services'
import { useConfigStore } from '@/stores/configStore'
import ServiceConfigCard from '@/components/services/ServiceConfigCard'

/**
 * 服务类型图标映射
 */
const serviceTypeIcons = {
  [ServiceType.LLM]: Zap,
  [ServiceType.WEB_CRAWLER]: Globe,
  [ServiceType.KNOWLEDGE_GRAPH]: Database,
  [ServiceType.LOCAL_MODEL]: Server,
}

/**
 * 服务类型标签映射
 */
const serviceTypeLabels = {
  [ServiceType.LLM]: '大语言模型',
  [ServiceType.WEB_CRAWLER]: '网页爬取',
  [ServiceType.KNOWLEDGE_GRAPH]: '知识图谱',
  [ServiceType.LOCAL_MODEL]: '本地模型',
}

/**
 * 状态统计组件
 */
const StatusCard: React.FC<{
  title: string
  count: number
  icon: React.ComponentType<{ className?: string }>
  color: string
}> = ({ title, count, icon: Icon, color }) => (
  <div className="card">
    <div className="card-content p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold">{count}</p>
        </div>
        <Icon className={cn('h-8 w-8', color)} />
      </div>
    </div>
  </div>
)

/**
 * 服务配置页面组件
 */
const ServiceConfigurationPage: React.FC = () => {
  const { 
    services, 
    isLoading, 
    error, 
    addService, 
    exportServices,
    importServices,
    resetServices,
    getServiceTemplates
  } = useConfigStore()
  
  // 获取服务模板
  const serviceTemplates = getServiceTemplates()

  // 状态管理
  const [selectedType, setSelectedType] = useState<ServiceType | 'all'>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [showImportDialog, setShowImportDialog] = useState(false)
  const [importData, setImportData] = useState('')

  // 计算统计数据
  const stats = useMemo(() => {
    if (!services || !Array.isArray(services)) {
      return { total: 0, connected: 0, disconnected: 0, error: 0 }
    }
    
    const total = services.length
    const connected = services.filter(s => s.status === ServiceStatus.CONNECTED).length
    const disconnected = services.filter(s => s.status === ServiceStatus.DISCONNECTED).length
    const error = services.filter(s => s.status === ServiceStatus.ERROR).length

    return { total, connected, disconnected, error }
  }, [services])

  // 过滤服务模板
  const filteredTemplates = useMemo(() => {
    if (!serviceTemplates || !Array.isArray(serviceTemplates)) {
      return []
    }
    
    return serviceTemplates.filter(template => {
      const matchesType = selectedType === 'all' || template.type === selectedType
      const matchesSearch = searchQuery === '' || 
        template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        template.description.toLowerCase().includes(searchQuery.toLowerCase())
      
      return matchesType && matchesSearch
    })
  }, [serviceTemplates, selectedType, searchQuery])

  // 过滤已配置的服务
  const filteredServices = useMemo(() => {
    if (!services || !Array.isArray(services)) {
      return []
    }
    
    return services.filter(service => {
      const matchesType = selectedType === 'all' || service.type === selectedType
      const matchesSearch = searchQuery === '' || 
        service.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        service.description.toLowerCase().includes(searchQuery.toLowerCase())
      
      return matchesType && matchesSearch
    })
  }, [services, selectedType, searchQuery])

  /**
   * 处理导出配置
   */
  const handleExport = () => {
    const config = exportServices()
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `service-config-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  /**
   * 处理导入配置
   */
  const handleImport = () => {
    try {
      const config = JSON.parse(importData)
      importServices(config)
      setShowImportDialog(false)
      setImportData('')
    } catch (error) {
      alert('导入失败：配置文件格式不正确')
    }
  }

  /**
   * 处理文件上传
   */
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const content = e.target?.result as string
        setImportData(content)
      }
      reader.readAsText(file)
    }
  }

  /**
   * 处理重置配置
   */
  const handleReset = () => {
    if (confirm('确定要重置所有配置吗？此操作无法撤销。')) {
      resetServices()
    }
  }

  return (
    <>
      <Helmet>
        <title>服务配置 - Shrimp Agent</title>
        <meta name="description" content="配置和管理外部服务集成" />
      </Helmet>

      <div className="container mx-auto p-6 space-y-6">
        {/* 页面标题 */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center space-x-2">
              <Settings className="h-8 w-8" />
              <span>服务配置</span>
            </h1>
            <p className="text-muted-foreground mt-1">
              配置和管理外部服务集成，包括大语言模型、网页爬取、知识图谱和本地模型服务
            </p>
          </div>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-500" />
              <span className="text-red-700">{error}</span>
            </div>
          </div>
        )}

        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatusCard
            title="总服务数"
            count={stats.total}
            icon={Settings}
            color="text-blue-500"
          />
          <StatusCard
            title="已连接"
            count={stats.connected}
            icon={CheckCircle}
            color="text-green-500"
          />
          <StatusCard
            title="未连接"
            count={stats.disconnected}
            icon={XCircle}
            color="text-gray-500"
          />
          <StatusCard
            title="连接失败"
            count={stats.error}
            icon={AlertCircle}
            color="text-red-500"
          />
        </div>

        {/* 过滤器和操作栏 */}
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex flex-col sm:flex-row gap-4 flex-1">
            {/* 搜索框 */}
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                className="input pl-10"
                placeholder="搜索服务..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            {/* 类型过滤器 */}
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <select
                className="input min-w-[120px]"
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value as ServiceType | 'all')}
              >
                <option value="all">所有类型</option>
                {Object.entries(serviceTypeLabels).map(([type, label]) => (
                  <option key={type} value={type}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="flex space-x-2">
            <button
              className="btn btn-outline btn-sm"
              onClick={handleExport}
              disabled={services.length === 0}
            >
              <Download className="h-4 w-4 mr-1" />
              导出配置
            </button>
            
            <button
              className="btn btn-outline btn-sm"
              onClick={() => setShowImportDialog(true)}
            >
              <Upload className="h-4 w-4 mr-1" />
              导入配置
            </button>
            
            <button
              className="btn btn-outline btn-sm"
              onClick={handleReset}
              disabled={services.length === 0}
            >
              <RotateCcw className="h-4 w-4 mr-1" />
              重置配置
            </button>
          </div>
        </div>

        {/* 加载状态 */}
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="loading-spinner"></div>
            <span className="ml-2">加载中...</span>
          </div>
        )}

        {/* 已配置的服务 */}
        {!isLoading && filteredServices.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">已配置的服务</h2>
            <div className="grid gap-4">
              {filteredServices.map(service => {
                const template = serviceTemplates.find(t => t.type === service.type)
                if (!template) return null
                
                return (
                  <ServiceConfigCard
                    key={service.id}
                    template={template}
                    config={service}
                  />
                )
              })}
            </div>
          </div>
        )}

        {/* 可用的服务模板 */}
        {!isLoading && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">可用的服务</h2>
            <div className="grid gap-4">
              {filteredTemplates.map(template => {
                // 检查是否已经配置了此类型的服务
                const existingService = services.find(s => s.type === template.type && s.name === template.name)
                
                return (
                  <ServiceConfigCard
                    key={template.id}
                    template={template}
                    config={existingService}
                    onSave={addService}
                  />
                )
              })}
            </div>
          </div>
        )}

        {/* 空状态 */}
        {!isLoading && filteredServices.length === 0 && filteredTemplates.length === 0 && (
          <div className="text-center py-12">
            <Settings className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">没有找到匹配的服务</h3>
            <p className="text-muted-foreground">
              尝试调整搜索条件或选择不同的服务类型
            </p>
          </div>
        )}
      </div>

      {/* 导入配置对话框 */}
      {showImportDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">导入配置</h3>
            
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">选择配置文件</label>
                <input
                  type="file"
                  accept=".json"
                  onChange={handleFileUpload}
                  className="input"
                />
              </div>
              
              <div>
                <label className="text-sm font-medium mb-2 block">或粘贴配置内容</label>
                <textarea
                  className="input min-h-[200px] resize-none font-mono text-sm"
                  value={importData}
                  onChange={(e) => setImportData(e.target.value)}
                  placeholder="粘贴JSON配置内容..."
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-2 mt-6">
              <button
                className="btn btn-outline"
                onClick={() => {
                  setShowImportDialog(false)
                  setImportData('')
                }}
              >
                取消
              </button>
              <button
                className="btn btn-primary"
                onClick={handleImport}
                disabled={!importData.trim()}
              >
                导入
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default ServiceConfigurationPage