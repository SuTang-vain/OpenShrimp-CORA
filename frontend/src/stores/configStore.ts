import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { 
  ServiceConfig, 
  ServiceType, 
  ServiceStatus, 
  ServiceTestResult,
  ServiceTemplate,
  LLMServiceConfig,
  WebCrawlerServiceConfig,
  KnowledgeGraphServiceConfig,
  LocalModelServiceConfig
} from '@/types/services'

/**
 * 配置状态管理接口
 */
interface ConfigState {
  // 服务配置
  services: ServiceConfig[]
  
  // UI状态
  isLoading: boolean
  error: string | null
  
  // 操作方法
  addService: (service: ServiceConfig) => void
  updateService: (id: string, updates: Partial<ServiceConfig>) => void
  removeService: (id: string) => void
  toggleService: (id: string) => void
  
  // 测试相关
  testService: (id: string) => Promise<ServiceTestResult>
  updateServiceStatus: (id: string, status: ServiceStatus, errorMessage?: string) => void
  
  // 批量操作
  importServices: (services: ServiceConfig[]) => void
  exportServices: () => ServiceConfig[]
  resetServices: () => void
  
  // 工具方法
  getServiceById: (id: string) => ServiceConfig | undefined
  getServicesByType: (type: ServiceType) => ServiceConfig[]
  getEnabledServices: () => ServiceConfig[]
  
  // 设置状态
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  
  // 获取服务模板
  getServiceTemplates: () => ServiceTemplate[]
}

/**
 * 预定义服务模板
 */
export const serviceTemplates: ServiceTemplate[] = [
  // LLM服务模板
  {
    id: 'modelscope',
    name: 'ModelScope',
    type: ServiceType.LLM,
    description: '阿里云魔搭社区提供的大语言模型服务，支持多种开源模型。',
    officialUrl: 'https://modelscope.cn',
    setupInstructions: [
      '前往 ModelScope 官网注册账号',
      '在控制台中创建 API Key',
      '复制 API Key 并粘贴到下方输入框',
      '选择合适的模型进行配置'
    ],
    defaultConfig: {
      baseUrl: 'https://dashscope.aliyuncs.com/api/v1',
      model: 'qwen-turbo',
      maxTokens: 2000,
      temperature: 0.7
    },
    requiredFields: ['apiKey'],
    optionalFields: ['baseUrl', 'model', 'maxTokens', 'temperature'],
    icon: '🤖',
    tags: ['LLM', '阿里云', '开源']
  },
  {
    id: 'zhipu-ai',
    name: '智谱AI (GLM)',
    type: ServiceType.LLM,
    description: '智谱AI提供的GLM系列大语言模型服务，支持GLM-4等先进模型。',
    officialUrl: 'https://open.bigmodel.cn',
    setupInstructions: [
      '前往智谱AI开放平台注册账号',
      '在API管理中创建新的API Key',
      '复制API Key并粘贴到下方输入框',
      '根据需要选择GLM模型版本'
    ],
    defaultConfig: {
      baseUrl: 'https://open.bigmodel.cn/api/paas/v4',
      model: 'glm-4',
      maxTokens: 2000,
      temperature: 0.7
    },
    requiredFields: ['apiKey'],
    optionalFields: ['baseUrl', 'model', 'maxTokens', 'temperature'],
    icon: '🧠',
    tags: ['LLM', '智谱AI', 'GLM']
  },
  {
    id: 'deepseek',
    name: 'DeepSeek',
    type: ServiceType.LLM,
    description: 'DeepSeek提供的高性能大语言模型服务，专注于代码和推理能力。',
    officialUrl: 'https://platform.deepseek.com',
    setupInstructions: [
      '前往DeepSeek平台注册账号',
      '在API Keys页面创建新的密钥',
      '复制API Key并粘贴到下方输入框',
      '选择适合的DeepSeek模型'
    ],
    defaultConfig: {
      baseUrl: 'https://api.deepseek.com/v1',
      model: 'deepseek-chat',
      maxTokens: 2000,
      temperature: 0.7
    },
    requiredFields: ['apiKey'],
    optionalFields: ['baseUrl', 'model', 'maxTokens', 'temperature'],
    icon: '🔍',
    tags: ['LLM', 'DeepSeek', '代码']
  },
  
  // 网页爬取服务模板
  {
    id: 'firecrawl',
    name: 'Firecrawl',
    type: ServiceType.WEB_CRAWLER,
    description: '专业的网页内容抓取和解析服务，支持JavaScript渲染和智能内容提取。',
    officialUrl: 'https://firecrawl.dev',
    setupInstructions: [
      '前往Firecrawl官网注册账号',
      '在Dashboard中获取API Key',
      '复制API Key并粘贴到下方输入框',
      '配置爬取参数和限制'
    ],
    defaultConfig: {
      baseUrl: 'https://api.firecrawl.dev',
      maxPages: 10,
      timeout: 30000
    },
    requiredFields: ['apiKey'],
    optionalFields: ['baseUrl', 'maxPages', 'timeout'],
    icon: '🕷️',
    tags: ['爬虫', 'JavaScript', '内容提取']
  },
  
  // 知识图谱数据库模板
  {
    id: 'neo4j-aura',
    name: 'Neo4j Aura',
    type: ServiceType.KNOWLEDGE_GRAPH,
    description: 'Neo4j官方云服务，提供托管的图数据库解决方案。',
    officialUrl: 'https://neo4j.com/cloud/aura',
    setupInstructions: [
      '前往 Neo4j Aura 注册账号并创建数据库实例',
      '在 Aura 控制台的 Connect 页面复制连接 URL（格式：neo4j+s://<instance-id>.databases.neo4j.io）',
      '用户名通常为 neo4j；密码为创建实例时设置的登录密码',
      '数据库名默认为 neo4j；如使用多数据库请填写目标数据库名',
      '在下方表单填写 connectionUrl、username、password 与可选的 database 字段并保存',
      '点击“测试连接”验证连通性（凭据会安全保存到后端的加密存储）',
      '如遇连接失败：检查网络是否可访问 *.databases.neo4j.io、确认未被公司防火墙阻断、并确保使用 neo4j+s 安全协议'
    ],
    defaultConfig: {
      authType: 'basic',
      database: 'neo4j'
    },
    requiredFields: ['connectionUrl', 'username', 'password'],
    optionalFields: ['database'],
    icon: '🕸️',
    tags: ['图数据库', 'Neo4j', '云服务']
  },
  {
    id: 'neo4j-local',
    name: 'Neo4j 本地实例',
    type: ServiceType.KNOWLEDGE_GRAPH,
    description: '本地部署的Neo4j数据库实例，适合开发和测试环境。',
    officialUrl: 'https://neo4j.com/download',
    setupInstructions: [
      '下载并安装 Neo4j Desktop 或 Community 版本，创建并启动本地数据库',
      '首次启动时设置管理员密码；默认用户名为 neo4j',
      '确认监听地址为 bolt://localhost:7687（本地默认端口为 7687）',
      '在下方表单填写 connectionUrl（如 bolt://localhost:7687）、username（neo4j）、password，以及可选的 database（默认 neo4j）',
      '保存后点击“测试连接”，后端将尝试连接并校验基础 Schema',
      '如测试失败：检查数据库是否已启动、端口是否开放、以及是否与后端服务在同一网络可达'
    ],
    defaultConfig: {
      connectionUrl: 'bolt://localhost:7687',
      authType: 'basic',
      username: 'neo4j',
      database: 'neo4j'
    },
    requiredFields: ['connectionUrl', 'username', 'password'],
    optionalFields: ['database'],
    icon: '💾',
    tags: ['图数据库', 'Neo4j', '本地部署']
  },
  
  // 本地模型服务模板
  {
    id: 'ollama',
    name: 'Ollama',
    type: ServiceType.LOCAL_MODEL,
    description: '本地运行大语言模型的轻量级工具，支持多种开源模型。',
    officialUrl: 'https://ollama.ai',
    setupInstructions: [
      '下载并安装Ollama客户端',
      '使用命令行拉取所需模型（如：ollama pull llama2）',
      '启动Ollama服务',
      '确保服务运行在http://localhost:11434'
    ],
    defaultConfig: {
      baseUrl: 'http://localhost:11434',
      healthCheckUrl: 'http://localhost:11434/api/tags'
    },
    requiredFields: ['baseUrl'],
    optionalFields: ['healthCheckUrl', 'apiKey'],
    icon: '🦙',
    tags: ['本地模型', 'Ollama', '开源']
  },
  {
    id: 'lm-studio',
    name: 'LM Studio',
    type: ServiceType.LOCAL_MODEL,
    description: '用户友好的本地大语言模型运行环境，提供图形界面和API服务。',
    officialUrl: 'https://lmstudio.ai',
    setupInstructions: [
      '下载并安装LM Studio',
      '在模型库中下载所需模型',
      '启动本地服务器',
      '确认API服务地址（通常为http://localhost:1234/v1）'
    ],
    defaultConfig: {
      baseUrl: 'http://localhost:1234/v1',
      healthCheckUrl: 'http://localhost:1234/v1/models'
    },
    requiredFields: ['baseUrl'],
    optionalFields: ['healthCheckUrl', 'apiKey'],
    icon: '🎛️',
    tags: ['本地模型', 'LM Studio', '图形界面']
  }
]

/**
 * 创建配置状态管理
 */
export const useConfigStore = create<ConfigState>()(
  persist(
    (set, get) => ({
      // 初始状态
      services: [],
      isLoading: false,
      error: null,

      // 服务管理
      addService: (service) => {
        set((state) => ({
          services: [...state.services, service]
        }))
      },

      updateService: (id, updates) => {
        set((state) => ({
          services: state.services.map(service =>
            service.id === id ? { ...service, ...updates } : service
          )
        }))
      },

      removeService: (id) => {
        set((state) => ({
          services: state.services.filter(service => service.id !== id)
        }))
      },

      toggleService: (id) => {
        set((state) => ({
          services: state.services.map(service =>
            service.id === id ? { ...service, enabled: !service.enabled } : service
          )
        }))
      },

      // 测试服务
      testService: async (id) => {
        const service = get().getServiceById(id)
        if (!service) {
          return { success: false, message: '服务不存在' }
        }

        get().updateServiceStatus(id, ServiceStatus.TESTING)

        try {
          // 这里应该调用实际的API测试逻辑
          // 暂时模拟测试结果
          await new Promise(resolve => setTimeout(resolve, 2000))
          
          const success = Math.random() > 0.3 // 70%成功率模拟
          const result: ServiceTestResult = {
            success,
            message: success ? '连接成功' : '连接失败：无法访问服务',
            responseTime: Math.floor(Math.random() * 1000) + 100
          }

          get().updateServiceStatus(
            id, 
            success ? ServiceStatus.CONNECTED : ServiceStatus.ERROR,
            success ? undefined : result.message
          )

          return result
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : '未知错误'
          get().updateServiceStatus(id, ServiceStatus.ERROR, errorMessage)
          return { success: false, message: errorMessage }
        }
      },

      updateServiceStatus: (id, status, errorMessage) => {
        set((state) => ({
          services: state.services.map(service =>
            service.id === id 
              ? { 
                  ...service, 
                  status, 
                  errorMessage,
                  lastTested: new Date()
                } 
              : service
          )
        }))
      },

      // 批量操作
      importServices: (services) => {
        set({ services })
      },

      exportServices: () => {
        return get().services
      },

      resetServices: () => {
        set({ services: [] })
      },

      // 工具方法
      getServiceById: (id) => {
        return get().services.find(service => service.id === id)
      },

      getServicesByType: (type) => {
        return get().services.filter(service => service.type === type)
      },

      getEnabledServices: () => {
        return get().services.filter(service => service.enabled)
      },

      // 状态设置
      setLoading: (loading) => {
        set({ isLoading: loading })
      },

      setError: (error) => {
        set({ error })
      },

      // 获取服务模板
      getServiceTemplates: () => {
        return serviceTemplates
      }
    }),
    {
      name: 'config-store',
      // 只持久化服务配置，不持久化UI状态
      partialize: (state) => ({ services: state.services })
    }
  )
)