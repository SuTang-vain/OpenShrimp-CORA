import * as React from 'react'
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import type { User, AuthState, LoginRequest, RegisterRequest } from '@/types'
import { authApi } from '@/api/auth'

/**
 * 认证操作接口
 */
interface AuthActions {
  login: (credentials: LoginRequest) => Promise<void>
  register: (userData: RegisterRequest) => Promise<void>
  logout: () => void
  refreshTokenAction: () => Promise<void>
  updateUser: (userData: Partial<User>) => void
  initializeAuth: () => Promise<void>
  clearAuth: () => void
}

/**
 * 认证状态管理
 */
export const useAuthStore = create<AuthState & AuthActions>()(
  persist(
    (set, get) => ({
      // 初始状态
      isAuthenticated: false,
      user: null,
      token: null,
      refreshToken: null,

      // 登录
      login: async (credentials: LoginRequest) => {
        try {
          const response = await authApi.login(credentials)
          console.debug('[authStore.login] api response', response)

          // 兼容后端字段（access_token/refresh_token 与 data.token/refreshToken）
          const apiData: any = response as any
          const user = apiData?.user || apiData?.data?.user
          const token = apiData?.access_token || apiData?.token || apiData?.data?.token
          const refreshToken = apiData?.refresh_token || apiData?.refreshToken || apiData?.data?.refreshToken

          // 只要有有效的 token 和 user 就视为成功
          const hasValidData = !!(token && user)
          console.debug('[authStore.login] extracted', { hasValidData, user, token, refreshToken })

          if (hasValidData) {
            set({
              isAuthenticated: true,
              user,
              token,
              refreshToken,
            })

            // 设置 API 默认 token
            authApi.setAuthToken(token)

            // 触发登录事件
            window.dispatchEvent(new CustomEvent('auth-login', { detail: { user } }))
          } else {
            const rawMessage = (response as any)?.error || (response as any)?.message || ''
            const errorMessage = rawMessage && !/成功/.test(rawMessage) ? rawMessage : '用户名或密码错误'
            throw new Error(errorMessage || '登录失败')
          }
        } catch (error: any) {
          const rawMessage = (error as any)?.error || (error as any)?.message || ''
          const errorMessage = rawMessage && !/成功/.test(rawMessage) ? rawMessage : '登录失败'
          console.error('登录失败:', errorMessage)
          throw new Error(errorMessage)
        }
      },

      // 注册
      register: async (userData: RegisterRequest) => {
        try {
          const response = await authApi.register(userData)
          console.debug('[authStore.register] api response', response)

          // 兼容后端字段（access_token/refresh_token 与 data.token/refreshToken），并允许仅返回 user
          const apiData: any = response as any
          const user = apiData?.user || apiData?.data?.user
          const token = apiData?.access_token || apiData?.token || apiData?.data?.token
          const refreshToken = apiData?.refresh_token || apiData?.refreshToken || apiData?.data?.refreshToken

          const isSuccess = !!((response as any)?.success) || (response as any)?.code === 200
          console.debug('[authStore.register] extracted', { isSuccess, user, token, refreshToken })

          if (isSuccess && user) {
            // 如果后端返回了 token，则自动登录；否则仅视为注册成功（不抛错）
            if (token) {
              set({
                isAuthenticated: true,
                user,
                token,
                refreshToken,
              })
              authApi.setAuthToken(token)
            }

            // 触发注册事件（页面可根据事件提示并跳转到登录页）
            window.dispatchEvent(new CustomEvent('auth-register', { detail: { user } }))
            return
          } else {
            const rawMessage = (response as any)?.error || (response as any)?.message || ''
            const errorMessage = rawMessage && !/成功/.test(rawMessage) ? rawMessage : '注册失败'
            throw new Error(errorMessage)
          }
        } catch (error: any) {
          const rawMessage = (error as any)?.error || (error as any)?.message || ''
          const errorMessage = rawMessage && !/成功/.test(rawMessage) ? rawMessage : '注册失败'
          console.error('注册失败:', errorMessage)
          throw new Error(errorMessage)
        }
      },

      // 登出
      logout: async () => {
        try {
          const { user } = get()
          
          // 调用登出 API
          await authApi.logout()
          
          // 清除状态
          set({
            isAuthenticated: false,
            user: null,
            token: null,
            refreshToken: null,
          })
          
          // 清除 API token
          authApi.clearAuthToken()
          
          // 触发登出事件
          window.dispatchEvent(
            new CustomEvent('auth-logout', {
              detail: { user },
            })
          )
        } catch (error) {
          console.error('登出失败:', error)
          // 即使 API 调用失败，也要清除本地状态
          get().clearAuth()
        }
      },

      // 刷新 token
      refreshTokenAction: async () => {
        try {
          const { refreshToken: currentRefreshToken } = get()
          
          if (!currentRefreshToken) {
            throw new Error('没有刷新令牌')
          }
          
          const response = await authApi.refreshToken(currentRefreshToken)
          
          if (response.success && response.data) {
            const { token, refreshToken: newRefreshToken } = response.data
            
            set({
              token,
              refreshToken: newRefreshToken,
            })
            
            // 更新 API token
            authApi.setAuthToken(token)
          } else {
            throw new Error(response.message || '刷新令牌失败')
          }
        } catch (error) {
          console.error('刷新令牌失败:', error)
          // 刷新失败，清除认证状态
          get().clearAuth()
          throw error
        }
      },

      // 更新用户信息
      updateUser: (userData: Partial<User>) => {
        const { user } = get()
        
        if (user) {
          set({
            user: { ...user, ...userData },
          })
          
          // 触发用户更新事件
          window.dispatchEvent(
            new CustomEvent('auth-user-updated', {
              detail: { user: { ...user, ...userData } },
            })
          )
        }
      },

      // 初始化认证状态
      initializeAuth: async () => {
        try {
          const { token } = get()
          
          if (token) {
            // 设置 API token
            authApi.setAuthToken(token)
            
            try {
              // 验证 token 有效性
              const response = await authApi.getCurrentUser()
              
              if (response.success && response.data) {
                set({
                  isAuthenticated: true,
                  user: response.data,
                })
              } else {
                // Token 无效，尝试刷新
                if (get().refreshToken) {
                  await get().refreshTokenAction()
                } else {
                  get().clearAuth()
                }
              }
            } catch (error) {
              // Token 验证失败，尝试刷新
              if (get().refreshToken) {
                try {
                  await get().refreshTokenAction()
                } catch (refreshError) {
                  get().clearAuth()
                }
              } else {
                get().clearAuth()
              }
            }
          }
        } catch (error) {
          console.error('初始化认证状态失败:', error)
          get().clearAuth()
        }
      },

      // 清除认证状态
      clearAuth: () => {
        set({
          isAuthenticated: false,
          user: null,
          token: null,
          refreshToken: null,
        })
        
        // 清除 API token
        authApi.clearAuthToken()
      },
    }),
    {
      name: 'shrimp-auth-storage',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
    }
  )
)

/**
 * 认证相关的工具函数
 */
export const authUtils = {
  /**
   * 检查用户是否已登录
   */
  isLoggedIn: (): boolean => {
    return useAuthStore.getState().isAuthenticated
  },
  
  /**
   * 获取当前用户
   */
  getCurrentUser: (): User | null => {
    return useAuthStore.getState().user
  },
  
  /**
   * 获取当前用户 ID
   */
  getCurrentUserId: (): string | null => {
    const user = useAuthStore.getState().user
    return user?.id || null
  },
  
  /**
   * 检查用户角色
   */
  hasRole: (role: string): boolean => {
    const user = useAuthStore.getState().user
    return user?.role === role
  },
  
  /**
   * 检查用户权限
   */
  hasPermission: (_permission: string): boolean => {
    const user = useAuthStore.getState().user
    // 这里可以根据实际的权限系统实现
    return user?.role === 'admin' || false
  },
  
  /**
   * 获取认证 token
   */
  getToken: (): string | null => {
    return useAuthStore.getState().token
  },
  
  /**
   * 获取用户头像 URL
   */
  getAvatarUrl: (): string | null => {
    const user = useAuthStore.getState().user
    return user?.avatar || null
  },
  
  /**
   * 获取用户显示名称
   */
  getDisplayName: (): string => {
    const user = useAuthStore.getState().user
    return user?.username || user?.email || '未知用户'
  },
}

/**
 * React Hook 用于监听认证状态变化
 */
export const useAuthEffect = (callback: (isAuthenticated: boolean, user: User | null) => void) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const user = useAuthStore((state) => state.user)
  
  React.useEffect(() => {
    callback(isAuthenticated, user)
  }, [isAuthenticated, user, callback])
}

/**
 * React Hook 用于获取认证状态
 */
export const useAuth = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const user = useAuthStore((state) => state.user)
  const login = useAuthStore((state) => state.login)
  const register = useAuthStore((state) => state.register)
  const logout = useAuthStore((state) => state.logout)
  const updateUser = useAuthStore((state) => state.updateUser)
  
  return {
    isAuthenticated,
    user,
    login,
    register,
    logout,
    updateUser,
    ...authUtils,
  }
}