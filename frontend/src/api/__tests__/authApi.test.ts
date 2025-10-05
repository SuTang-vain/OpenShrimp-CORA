/**
 * AuthApi 测试
 */
import { apiClient } from '../client'
import authApi, { authApi as namedAuthApi } from '../auth'
import type { ApiResponse } from '@/types'

jest.mock('../client', () => {
  const instance = {
    post: jest.fn(),
    get: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    setAuthToken: jest.fn(),
    clearAuthToken: jest.fn(),
  }
  return { apiClient: instance }
})

describe('AuthApi', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('login 成功时设置 token 并返回响应', async () => {
    const mockResponse: ApiResponse<any> = {
      success: true,
      data: {
        user: { id: '1', username: 'u', email: 'e', role: 'user', createdAt: '', updatedAt: '' },
        token: 'tkn',
        refreshToken: 'rtk',
        expiresIn: 3600,
      },
      code: 200,
    }
    ;(apiClient.post as jest.Mock).mockResolvedValueOnce(mockResponse)

    const res = await authApi.login({ username: 'u', password: 'p', rememberMe: true })

    expect(apiClient.post).toHaveBeenCalledWith('/auth/login', {
      username: 'u',
      password: 'p',
      rememberMe: true,
    })
    expect(apiClient.setAuthToken).toHaveBeenCalledWith('tkn')
    expect(res).toBe(mockResponse)
  })

  it('login 失败时抛出错误，不崩溃', async () => {
    const error = new Error('网络错误')
    ;(apiClient.post as jest.Mock).mockRejectedValueOnce(error)

    await expect(
      authApi.login({ username: 'u', password: 'p' })
    ).rejects.toThrow('网络错误')
  })

  it('register 成功时设置 token', async () => {
    const mockResponse: ApiResponse<any> = {
      success: true,
      data: {
        user: { id: '1', username: 'u', email: 'e', role: 'user', createdAt: '', updatedAt: '' },
        token: 'tkn2',
        refreshToken: 'rtk2',
        expiresIn: 3600,
      },
      code: 200,
    }
    ;(apiClient.post as jest.Mock).mockResolvedValueOnce(mockResponse)

    const res = await authApi.register({ username: 'u', email: 'e', password: 'p', confirmPassword: 'p' })

    expect(apiClient.post).toHaveBeenCalledWith('/auth/register', {
      username: 'u', email: 'e', password: 'p', confirm_password: 'p'
    })
    expect(apiClient.setAuthToken).toHaveBeenCalledWith('tkn2')
    expect(res).toBe(mockResponse)
  })

  it('logout 成功时清除 token', async () => {
    const mockResponse: ApiResponse<void> = { success: true, data: undefined, code: 200 }
    ;(apiClient.post as jest.Mock).mockResolvedValueOnce(mockResponse)

    const res = await authApi.logout()

    expect(apiClient.post).toHaveBeenCalledWith('/auth/logout')
    expect(apiClient.clearAuthToken).toHaveBeenCalled()
    expect(res).toBe(mockResponse)
  })

  it('logout 失败时也应清除 token 并抛错', async () => {
    const error = new Error('服务器错误')
    ;(apiClient.post as jest.Mock).mockRejectedValueOnce(error)

    await expect(authApi.logout()).rejects.toThrow('服务器错误')
    expect(apiClient.clearAuthToken).toHaveBeenCalled()
  })

  it('refreshToken 成功时更新 token', async () => {
    const mockResponse: ApiResponse<any> = {
      success: true,
      data: { token: 'newTkn', refreshToken: 'newRtk', expiresIn: 3600 },
      code: 200,
    }
    ;(apiClient.post as jest.Mock).mockResolvedValueOnce(mockResponse)

    const res = await authApi.refreshToken('oldRtk')

    expect(apiClient.post).toHaveBeenCalledWith('/auth/refresh', { refresh_token: 'oldRtk' })
    expect(apiClient.setAuthToken).toHaveBeenCalledWith('newTkn')
    expect(res).toBe(mockResponse)
  })

  it('getCurrentUser 应调用 /auth/me', async () => {
    const mockResponse: ApiResponse<any> = { success: true, data: { id: '1' }, code: 200 }
    ;(apiClient.get as jest.Mock).mockResolvedValueOnce(mockResponse)

    const res = await authApi.getCurrentUser()

    expect(apiClient.get).toHaveBeenCalledWith('/auth/me')
    expect(res).toBe(mockResponse)
  })

  it('validateToken 在成功时返回 true，失败返回 false', async () => {
    const successResp: ApiResponse<any> = { success: true, data: { id: '1' }, code: 200 }
    ;(apiClient.get as jest.Mock).mockResolvedValueOnce(successResp)

    await expect(namedAuthApi.validateToken()).resolves.toBe(true)

    const failErr = new Error('401 Unauthorized')
    ;(apiClient.get as jest.Mock).mockRejectedValueOnce(failErr)

    await expect(namedAuthApi.validateToken()).resolves.toBe(false)
  })

  it('hasPermission 正确返回布尔值', async () => {
    const okResp: ApiResponse<any> = { success: true, data: { hasPermission: true }, code: 200 }
    ;(apiClient.get as jest.Mock).mockResolvedValueOnce(okResp)
    await expect(namedAuthApi.hasPermission('admin')).resolves.toBe(true)

    const failResp: ApiResponse<any> = { success: true, data: { hasPermission: false }, code: 200 }
    ;(apiClient.get as jest.Mock).mockResolvedValueOnce(failResp)
    await expect(namedAuthApi.hasPermission('user')).resolves.toBe(false)

    // 网络错误时返回 false
    const netErr = new Error('network error')
    ;(apiClient.get as jest.Mock).mockRejectedValueOnce(netErr)
    await expect(namedAuthApi.hasPermission('any')).resolves.toBe(false)
  })
})