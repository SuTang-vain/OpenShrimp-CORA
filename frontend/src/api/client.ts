import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { toast } from 'sonner'

import type { ApiResponse } from '@/types'

/**
 * API 客户端配置
 */
interface ApiClientConfig {
  baseURL: string
  timeout: number
  withCredentials: boolean
}

/**
 * 默认配置
 */
const defaultConfig: ApiClientConfig = {
  // 确保 baseURL 有前导斜杠；若配置为完整URL则原样使用
  baseURL: (() => {
    const v = (import.meta as any).env.VITE_API_BASE_URL
    if (!v || v.trim() === '') return '/api'
    // 完整URL直接使用
    if (/^https?:\/\//i.test(v)) return v
    // 规范相对路径：确保前导斜杠
    return v.startsWith('/') ? v : `/${v}`
  })(),
  timeout: 30000,
  withCredentials: true,
}

/**
 * 创建 API 客户端实例
 */
class ApiClient {
  private instance: AxiosInstance
  private authToken: string | null = null

  constructor(config: Partial<ApiClientConfig> = {}) {
    const finalConfig = { ...defaultConfig, ...config }

    this.instance = axios.create({
      baseURL: finalConfig.baseURL,
      timeout: finalConfig.timeout,
      withCredentials: finalConfig.withCredentials,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  /**
   * 设置拦截器
   */
  private setupInterceptors() {
    // 请求拦截器
    this.instance.interceptors.request.use(
      (config) => {
        // 添加认证 token
        if (this.authToken) {
          config.headers.Authorization = `Bearer ${this.authToken}`
        }

        // 添加请求 ID 用于追踪
        config.headers['X-Request-ID'] = this.generateRequestId()

        // 添加时间戳
        config.headers['X-Timestamp'] = Date.now().toString()

        // 开发环境下打印请求信息
        if ((import.meta as any).env.DEV) {
          // eslint-disable-next-line no-console
          console.log('🚀 API Request:', {
            method: config.method?.toUpperCase(),
            url: config.url,
            data: config.data,
            params: config.params,
          })
        }

        return config
      },
      (error) => {
        console.error('❌ Request Error:', error)
        return Promise.reject(error)
      }
    )

    // 响应拦截器
    this.instance.interceptors.response.use(
      (response) => {
        // 开发环境下打印响应信息
        if ((import.meta as any).env.DEV) {
          // eslint-disable-next-line no-console
          console.log('✅ API Response:', {
            status: response.status,
            url: response.config.url,
            data: response.data,
          })
        }

        return response
      },
      (error: AxiosError) => {
        return this.handleResponseError(error)
      }
    )
  }

  /**
   * 处理响应错误
   */
  private async handleResponseError(error: AxiosError): Promise<never> {
    const { response, request, message } = error

    // 开发环境下打印错误信息
    if ((import.meta as any).env.DEV) {
      console.error('❌ API Error:', {
        status: response?.status,
        url: error.config?.url,
        message,
        data: response?.data,
      })
    }

    if (response) {
      // 服务器响应错误
      const { status, data } = response

      switch (status) {
        case 401: {
          // 未授权，清除认证信息并跳转到登录页
          this.handleUnauthorized()
          break
        }

        case 403:
          // 禁止访问
          toast.error('访问被拒绝，您没有足够的权限')
          break

        case 404:
          // 资源不存在
          toast.error('请求的资源不存在')
          break

        case 422:
          // 验证错误
          this.handleValidationError(data)
          break

        case 429:
          // 请求过于频繁
          toast.error('请求过于频繁，请稍后再试')
          break

        case 500:
          // 服务器内部错误：优先提取后端提供的具体错误信息
          {
            const err = (data as any)
            const msg = err?.message || err?.error?.message || (typeof err?.error === 'string' ? err.error : undefined) || '服务器内部错误，请稍后再试'
            toast.error(msg)
          }
          break

        case 502:
        case 503:
        case 504:
          // 服务不可用
          toast.error('服务暂时不可用，请稍后再试')
          break

        default: {
          // 其他错误：兼容 error 为对象的场景
          const err = (data as any)
          let errorMessage = err?.message
          if (!errorMessage) {
            const e = err?.error
            if (typeof e === 'string') errorMessage = e
            else if (e && typeof e === 'object') errorMessage = e.message || JSON.stringify(e)
          }
          toast.error(errorMessage || '请求失败')
          break
        }
      }

      // 返回格式化的错误响应
      const err = (data as any)
      const normalizedMessage = err?.message || err?.error?.message || (typeof err?.error === 'string' ? err.error : undefined) || '请求失败'
      const apiError: ApiResponse = {
        success: false,
        error: normalizedMessage,
        code: status,
        data: data,
      }

      return Promise.reject(apiError)
    } else if (request) {
      // 网络错误
      toast.error('网络连接失败，请检查您的网络设置')
      
      const networkError: ApiResponse = {
        success: false,
        error: '网络连接失败',
        code: 0,
      }

      return Promise.reject(networkError)
    } else {
      // 其他错误
      toast.error('请求配置错误')
      
      const configError: ApiResponse = {
        success: false,
        error: message || '请求配置错误',
        code: -1,
      }

      return Promise.reject(configError)
    }
  }

  /**
   * 处理未授权错误
   */
  private handleUnauthorized() {
    // 清除认证 token
    this.authToken = null
    
    // 清除本地存储的认证信息
    localStorage.removeItem('shrimp-auth-storage')
    
    // 显示错误提示
    toast.error('登录已过期，请重新登录')
    
    // 触发全局未授权事件
    window.dispatchEvent(new CustomEvent('auth-unauthorized'))
    
    // 延迟跳转到登录页，避免在当前请求处理过程中跳转
    setTimeout(() => {
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }, 1000)
  }

  /**
   * 处理验证错误
   */
  private handleValidationError(data: any) {
    if (data?.errors && Array.isArray(data.errors)) {
      // 显示第一个验证错误
      const firstError = data.errors[0]
      toast.error(firstError.message || '数据验证失败')
    } else if (data?.message) {
      toast.error(data.message)
    } else {
      toast.error('数据验证失败')
    }
  }

  /**
   * 生成请求 ID
   */
  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * 设置认证 token
   */
  setAuthToken(token: string | null) {
    this.authToken = token
  }

  /**
   * 清除认证 token
   */
  clearAuthToken() {
    this.authToken = null
  }

  /**
   * GET 请求
   */
  async get<T = any>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.instance.get(url, config)
    return this.formatResponse(response)
  }

  /**
   * POST 请求
   */
  async post<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.instance.post(url, data, config)
    return this.formatResponse(response)
  }

  /**
   * PUT 请求
   */
  async put<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.instance.put(url, data, config)
    return this.formatResponse(response)
  }

  /**
   * PATCH 请求
   */
  async patch<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.instance.patch(url, data, config)
    return this.formatResponse(response)
  }

  /**
   * DELETE 请求
   */
  async delete<T = any>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.instance.delete(url, config)
    return this.formatResponse(response)
  }

  /**
   * 上传文件
   */
  async upload<T = any>(
    url: string,
    formData: FormData,
    config?: AxiosRequestConfig & {
      onUploadProgress?: (progressEvent: any) => void
    }
  ): Promise<ApiResponse<T>> {
    const response = await this.instance.post(url, formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...config?.headers,
      },
    })
    return this.formatResponse(response)
  }

  /**
   * 下载文件
   */
  async download(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<Blob> {
    const response = await this.instance.get(url, {
      ...config,
      responseType: 'blob',
    })
    return response.data
  }

  /**
   * 格式化响应数据
   */
  private formatResponse<T>(response: AxiosResponse): ApiResponse<T> {
    const { data, status } = response
    console.debug('[ApiClient] raw response', { status, data })

    // 如果响应数据已经是标准格式，直接返回
    if (data && typeof data === 'object' && 'success' in data) {
      console.debug('[ApiClient] passthrough response', data)
      return data as ApiResponse<T>
    }

    // 否则包装成标准格式
    const formatted: ApiResponse<T> = {
      success: status >= 200 && status < 300,
      data: data as T,
      code: status,
    }
    console.debug('[ApiClient] formatted response', formatted)
    return formatted
  }

  /**
   * 获取原始 axios 实例
   */
  getInstance(): AxiosInstance {
    return this.instance
  }
}

// 创建默认的 API 客户端实例
export const apiClient = new ApiClient()

// 导出 ApiClient 类供其他地方使用
export { ApiClient }
export type { ApiClientConfig }