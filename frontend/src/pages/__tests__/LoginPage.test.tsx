/**
 * LoginPage 组件测试
 */
import * as React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import LoginPage from '../LoginPage'

// 模拟 useNavigate
const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}))

// 默认将 useAuthEffect 设为 noop，并内联构建可控的 auth store 模拟（避免 hoist 引发未初始化错误）
jest.mock('@/stores/authStore', () => {
  const state: any = {
    isAuthenticated: false,
    user: null,
    token: null,
    refreshToken: null,
    login: jest.fn(),
    logout: jest.fn(),
    register: jest.fn(),
  }

  const useAuthStore = jest.fn((selector?: any) => {
    if (typeof selector === 'function') return selector(state)
    return state
  })
  ;(useAuthStore as any).getState = () => state
  ;(useAuthStore as any).setState = (partial: any) => Object.assign(state, partial)

  // 成功登录时更新状态
  state.login.mockImplementation(async (payload: any) => {
    Object.assign(state, {
      isAuthenticated: true,
      user: { id: '1', username: payload?.username || 'testuser', email: 'test@example.com' },
      token: 'mock-token',
      refreshToken: 'mock-refresh',
    })
  })

  return {
    useAuthStore,
    useAuthEffect: jest.fn(() => {}),
  }
})

// 工具函数：带路由渲染
const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>)
}

describe('LoginPage Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockNavigate.mockClear()
  })

  it('应该正确渲染基本元素', () => {
    renderWithRouter(<LoginPage />)

    expect(screen.getByText('欢迎登录')).toBeInTheDocument()
    expect(screen.getByText('使用您的账户登录以继续')).toBeInTheDocument()

    expect(screen.getByLabelText('用户名')).toBeInTheDocument()
    expect(screen.getByLabelText('密码')).toBeInTheDocument()

    // 提交按钮
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument()

    // 记住我
    const remember = screen.getByRole('checkbox', { name: /记住我/i })
    expect(remember).toBeInTheDocument()
    expect((remember as HTMLInputElement).checked).toBe(true)
  })

  it('应该进行表单校验并提示错误', async () => {
    renderWithRouter(<LoginPage />)

    // 直接提交空表单
    fireEvent.submit(screen.getByRole('button', { name: /登录/i }).closest('form')!)

    expect(await screen.findByText('请输入用户名')).toBeInTheDocument()
    expect(await screen.findByText('请输入密码')).toBeInTheDocument()

    // 输入短密码
    const usernameInput = screen.getByLabelText('用户名')
    const passwordInput = screen.getByLabelText('密码')

    fireEvent.change(usernameInput, { target: { value: 'user1' } })
    fireEvent.change(passwordInput, { target: { value: '123' } })

    // 再次提交
    fireEvent.submit(screen.getByRole('button', { name: /登录/i }).closest('form')!)

    expect(await screen.findByText('密码长度至少6位')).toBeInTheDocument()
  })

  it('应该支持显示/隐藏密码', () => {
    renderWithRouter(<LoginPage />)

    const passwordInput = screen.getByLabelText('密码') as HTMLInputElement
    expect(passwordInput.type).toBe('password')

    const toggleBtn = screen.getByRole('button', { name: /显示密码|隐藏密码/ })
    fireEvent.click(toggleBtn)
    expect(passwordInput.type).toBe('text')

    fireEvent.click(toggleBtn)
    expect(passwordInput.type).toBe('password')
  })

  it('应该支持记住我切换', () => {
    renderWithRouter(<LoginPage />)
    const remember = screen.getByRole('checkbox', { name: /记住我/i }) as HTMLInputElement
    expect(remember.checked).toBe(true)
    fireEvent.click(remember)
    expect(remember.checked).toBe(false)
  })

  it('登录成功后应导航到 /dashboard', async () => {
    renderWithRouter(<LoginPage />)

    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'admin' } })
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: '123456' } })

    // 提交
    fireEvent.submit(screen.getByRole('button', { name: /登录/i }).closest('form')!)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true })
    })

    // 不应该显示提交错误
    expect(screen.queryByText(/登录失败/)).toBeNull()
  })

  it('登录失败时应显示错误反馈且不导航', async () => {
    // 重新定义 authStore.login 抛错
    const mod = await import('@/stores/authStore')
    const useAuthStore: any = (mod as any).useAuthStore
    const current = useAuthStore.getState()
    current.login.mockImplementation(async () => {
      throw new Error('账号或密码错误')
    })

    renderWithRouter(<LoginPage />)

    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'admin' } })
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: '123456' } })

    fireEvent.submit(screen.getByRole('button', { name: /登录/i }).closest('form')!)

    expect(await screen.findByText('账号或密码错误')).toBeInTheDocument()
    expect(mockNavigate).not.toHaveBeenCalled()
  })
})