import { apiClient } from './client'
import type { ApiResponse, User, LoginRequest, RegisterRequest } from '@/types'

/**
 * 登录响应数据
 */
interface LoginResponse {
  user: User
  token: string
  refreshToken: string
  expiresIn: number
}

/**
 * 注册响应数据
 */
interface RegisterResponse {
  user: User
  token: string
  refreshToken: string
  expiresIn: number
}

/**
 * 刷新 token 响应数据
 */
interface RefreshTokenResponse {
  token: string
  refreshToken: string
  expiresIn: number
}

/**
 * 认证 API 类
 */
class AuthApi {
  /**
   * 用户登录
   */
  async login(credentials: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    try {
      const response = await apiClient.post<LoginResponse>('/auth/login', credentials)
      
      // 登录成功后设置 token
      if (response.success && response.data?.token) {
        this.setAuthToken(response.data.token)
      }
      
      return response
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }

  /**
   * 用户注册
   */
  async register(userData: RegisterRequest): Promise<ApiResponse<RegisterResponse>> {
    try {
      // 后端期望 confirm_password（下划线），前端是 confirmPassword（驼峰）
      const payload = {
        username: userData.username,
        email: userData.email,
        password: userData.password,
        confirm_password: userData.confirmPassword,
      }
      const response = await apiClient.post<RegisterResponse>('/auth/register', payload)
      
      // 注册成功后设置 token
      if (response.success && response.data?.token) {
        this.setAuthToken(response.data.token)
      }
      
      return response
    } catch (error) {
      console.error('注册失败:', error)
      throw error
    }
  }

  /**
   * 用户登出
   */
  async logout(): Promise<ApiResponse<void>> {
    try {
      const response = await apiClient.post<void>('/auth/logout')
      
      // 清除 token
      this.clearAuthToken()
      
      return response
    } catch (error) {
      console.error('登出失败:', error)
      // 即使 API 调用失败，也要清除本地 token
      this.clearAuthToken()
      throw error
    }
  }

  /**
   * 刷新访问令牌
   */
  async refreshToken(refreshToken: string): Promise<ApiResponse<RefreshTokenResponse>> {
    try {
      const response = await apiClient.post<RefreshTokenResponse>('/auth/refresh', {
        // 后端期望的键名为 refresh_token
        refresh_token: refreshToken,
      })
      
      // 更新 token
      if (response.success && response.data?.token) {
        this.setAuthToken(response.data.token)
      }
      
      return response
    } catch (error) {
      console.error('刷新令牌失败:', error)
      throw error
    }
  }

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<ApiResponse<User>> {
    try {
      return await apiClient.get<User>('/auth/me')
    } catch (error) {
      console.error('获取用户信息失败:', error)
      throw error
    }
  }

  /**
   * 更新用户信息
   */
  async updateUser(userData: Partial<User>): Promise<ApiResponse<User>> {
    try {
      return await apiClient.put<User>('/auth/me', userData)
    } catch (error) {
      console.error('更新用户信息失败:', error)
      throw error
    }
  }

  /**
   * 修改密码
   */
  async changePassword(data: {
    currentPassword: string
    newPassword: string
    confirmPassword: string
  }): Promise<ApiResponse<void>> {
    try {
      return await apiClient.post<void>('/auth/change-password', data)
    } catch (error) {
      console.error('修改密码失败:', error)
      throw error
    }
  }

  /**
   * 忘记密码
   */
  async forgotPassword(email: string): Promise<ApiResponse<void>> {
    try {
      return await apiClient.post<void>('/auth/forgot-password', { email })
    } catch (error) {
      console.error('发送重置密码邮件失败:', error)
      throw error
    }
  }

  /**
   * 重置密码
   */
  async resetPassword(data: {
    token: string
    password: string
    confirmPassword: string
  }): Promise<ApiResponse<void>> {
    try {
      return await apiClient.post<void>('/auth/reset-password', data)
    } catch (error) {
      console.error('重置密码失败:', error)
      throw error
    }
  }

  /**
   * 验证邮箱
   */
  async verifyEmail(token: string): Promise<ApiResponse<void>> {
    try {
      return await apiClient.post<void>('/auth/verify-email', { token })
    } catch (error) {
      console.error('验证邮箱失败:', error)
      throw error
    }
  }

  /**
   * 重新发送验证邮件
   */
  async resendVerificationEmail(): Promise<ApiResponse<void>> {
    try {
      return await apiClient.post<void>('/auth/resend-verification')
    } catch (error) {
      console.error('重新发送验证邮件失败:', error)
      throw error
    }
  }

  /**
   * 检查用户名是否可用
   */
  async checkUsernameAvailability(username: string): Promise<ApiResponse<{ available: boolean }>> {
    try {
      return await apiClient.get<{ available: boolean }>(`/auth/check-username/${username}`)
    } catch (error) {
      console.error('检查用户名可用性失败:', error)
      throw error
    }
  }

  /**
   * 检查邮箱是否可用
   */
  async checkEmailAvailability(email: string): Promise<ApiResponse<{ available: boolean }>> {
    try {
      return await apiClient.get<{ available: boolean }>(`/auth/check-email/${email}`)
    } catch (error) {
      console.error('检查邮箱可用性失败:', error)
      throw error
    }
  }

  /**
   * 获取用户会话信息
   */
  async getSessions(): Promise<ApiResponse<Array<{
    id: string
    deviceInfo: string
    ipAddress: string
    location: string
    lastActive: string
    current: boolean
  }>>> {
    try {
      return await apiClient.get('/auth/sessions')
    } catch (error) {
      console.error('获取会话信息失败:', error)
      throw error
    }
  }

  /**
   * 终止指定会话
   */
  async terminateSession(sessionId: string): Promise<ApiResponse<void>> {
    try {
      return await apiClient.delete(`/auth/sessions/${sessionId}`)
    } catch (error) {
      console.error('终止会话失败:', error)
      throw error
    }
  }

  /**
   * 终止所有其他会话
   */
  async terminateAllOtherSessions(): Promise<ApiResponse<void>> {
    try {
      return await apiClient.post('/auth/sessions/terminate-others')
    } catch (error) {
      console.error('终止其他会话失败:', error)
      throw error
    }
  }

  /**
   * 启用两步验证
   */
  async enableTwoFactor(): Promise<ApiResponse<{
    qrCode: string
    secret: string
    backupCodes: string[]
  }>> {
    try {
      return await apiClient.post('/auth/2fa/enable')
    } catch (error) {
      console.error('启用两步验证失败:', error)
      throw error
    }
  }

  /**
   * 确认两步验证
   */
  async confirmTwoFactor(code: string): Promise<ApiResponse<{
    backupCodes: string[]
  }>> {
    try {
      return await apiClient.post('/auth/2fa/confirm', { code })
    } catch (error) {
      console.error('确认两步验证失败:', error)
      throw error
    }
  }

  /**
   * 禁用两步验证
   */
  async disableTwoFactor(password: string): Promise<ApiResponse<void>> {
    try {
      return await apiClient.post('/auth/2fa/disable', { password })
    } catch (error) {
      console.error('禁用两步验证失败:', error)
      throw error
    }
  }

  /**
   * 生成新的备份码
   */
  async generateBackupCodes(): Promise<ApiResponse<{
    backupCodes: string[]
  }>> {
    try {
      return await apiClient.post('/auth/2fa/backup-codes')
    } catch (error) {
      console.error('生成备份码失败:', error)
      throw error
    }
  }

  /**
   * 设置认证 token
   */
  setAuthToken(token: string) {
    apiClient.setAuthToken(token)
  }

  /**
   * 清除认证 token
   */
  clearAuthToken() {
    apiClient.clearAuthToken()
  }

  /**
   * 验证 token 是否有效
   */
  async validateToken(): Promise<boolean> {
    try {
      const response = await this.getCurrentUser()
      return response.success
    } catch (error) {
      return false
    }
  }

  /**
   * 获取用户权限列表
   */
  async getUserPermissions(): Promise<ApiResponse<string[]>> {
    try {
      return await apiClient.get<string[]>('/auth/permissions')
    } catch (error) {
      console.error('获取用户权限失败:', error)
      throw error
    }
  }

  /**
   * 检查用户是否有指定权限
   */
  async hasPermission(permission: string): Promise<boolean> {
    try {
      const response = await apiClient.get<{ hasPermission: boolean }>(
        `/auth/permissions/check/${permission}`
      )
      return response.data?.hasPermission || false
    } catch (error) {
      console.error('检查权限失败:', error)
      return false
    }
  }
}

// 创建 API 实例
const authApi = new AuthApi()

// 导出实例
export { authApi }
export default authApi

// 导出类型
export type {
  LoginResponse,
  RegisterResponse,
  RefreshTokenResponse,
}