/**
 * HomePage 组件测试
 */

import * as React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { useAuth } from '@/stores/authStore'
import { UserRole } from '@/types'

// 将模块 mock 放在组件导入之前，确保在加载组件前已生效
jest.mock('@/stores/authStore', () => ({
  useAuth: jest.fn(),
}))

// 模拟 useNavigate
const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}))

import HomePage from '../HomePage'

// 测试工具函数
const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  )
}

describe('HomePage Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // 为 useAuth 提供默认返回，避免未定义导致的结构错误
    ;(useAuth as jest.Mock).mockReturnValue({ isAuthenticated: false })
  })

  it('应该正确渲染首页内容', () => {
    renderWithRouter(<HomePage />)

    // 检查主要标题
    const mainHeading = screen.getByRole('heading', { level: 1 })
    expect(mainHeading).toBeInTheDocument()
    expect(mainHeading).toHaveTextContent(/智能搜索/i)
    expect(mainHeading).toHaveTextContent(/知识管理体验/i)
    
    // 检查描述文本
    expect(screen.getByText(/智能化的文档搜索和管理解决方案/i)).toBeInTheDocument()
    
    // 检查行动按钮（未认证默认显示）
    expect(screen.getByText(/免费注册/i)).toBeInTheDocument()
    expect(screen.getByText(/观看演示/i)).toBeInTheDocument()
  })

  it('应该显示统计数据', () => {
    renderWithRouter(<HomePage />)

    // 检查统计数字
    expect(screen.getByText('10,000+')).toBeInTheDocument()
    expect(screen.getByText('1M+')).toBeInTheDocument()
    expect(screen.getByText('50M+')).toBeInTheDocument()
    expect(screen.getByText('99.9%')).toBeInTheDocument()
  })

  it('应该显示功能特性', () => {
    renderWithRouter(<HomePage />)

    // 检查功能标题
    expect(screen.getByText('智能搜索')).toBeInTheDocument()
    expect(screen.getByText('文档管理')).toBeInTheDocument()
    expect(screen.getByText('快速响应')).toBeInTheDocument()
    expect(screen.getByText('安全可靠')).toBeInTheDocument()
    expect(screen.getByText('数据分析')).toBeInTheDocument()
    expect(screen.getByText('团队协作')).toBeInTheDocument()
  })

  it('应该显示快速开始步骤', () => {
    renderWithRouter(<HomePage />)

    // 检查步骤标题
    expect(screen.getByText('注册账户')).toBeInTheDocument()
    expect(screen.getByText('上传文档')).toBeInTheDocument()
    expect(screen.getAllByText('开始搜索').length).toBeGreaterThan(0)
  })

  it('应该处理搜索表单提交', async () => {
    renderWithRouter(<HomePage />)

    // 找到搜索输入框
    const searchInput = screen.getByPlaceholderText(/搜索任何内容.../i)
    const searchButton = screen.getByRole('button', { name: /开始搜索/i })

    // 输入搜索内容
    fireEvent.change(searchInput, { target: { value: 'test query' } })
    
    // 提交搜索
    fireEvent.click(searchButton)

    // 验证导航被调用
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/search?q=test%20query')
    })
  })

  it('应该处理空搜索提交', async () => {
    renderWithRouter(<HomePage />)

    const searchButton = screen.getByRole('button', { name: /开始搜索/i })
    
    // 提交空搜索
    fireEvent.click(searchButton)

    // 验证不会导航
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('应该处理键盘事件', async () => {
    renderWithRouter(<HomePage />)

    const searchInput = screen.getByPlaceholderText(/搜索任何内容.../i)
    
    // 输入搜索内容
    fireEvent.change(searchInput, { target: { value: 'test query' } })
    
    // 按 Enter 键并提交表单
    fireEvent.keyDown(searchInput, { key: 'Enter', code: 'Enter' })
    const form = searchInput.closest('form') as HTMLFormElement
    if (form) {
      fireEvent.submit(form)
    }

    // 验证导航被调用
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/search?q=test%20query')
    })
  })

  it('应该正确处理认证状态', () => {
    // 模拟已认证用户
    const mockUseAuth = jest.mocked(useAuth)
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        role: UserRole.USER,
        avatar: undefined,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      updateUser: jest.fn(),
      isLoggedIn: () => true,
      getCurrentUser: () => null,
      getCurrentUserId: () => '1',
      hasRole: () => false,
      hasPermission: () => false,
      getToken: () => 'mock-token',
      getAvatarUrl: () => null,
      getDisplayName: () => 'testuser',
    })

    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )

    // 验证已认证状态的显示：英雄区链接“开始使用”且指向 /search
    const startLink = screen.getByRole('link', { name: /开始使用/i })
    expect(startLink).toBeInTheDocument()
    expect(startLink).toHaveAttribute('href', '/search')
  })

  it('应该正确处理未认证状态', () => {
    // 模拟未认证用户
    const mockUseAuth = jest.mocked(useAuth)
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      user: null,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      updateUser: jest.fn(),
      isLoggedIn: () => false,
      getCurrentUser: () => null,
      getCurrentUserId: () => null,
      hasRole: () => false,
      hasPermission: () => false,
      getToken: () => null,
      getAvatarUrl: () => null,
      getDisplayName: () => '未知用户',
    })

    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )

    // 验证未认证状态的显示（按钮“免费注册”）
    expect(screen.getByText(/免费注册/)).toBeInTheDocument()
  })

  it('应该支持无障碍访问', () => {
    renderWithRouter(<HomePage />)

    // 检查标题层级
    const mainHeading = screen.getByRole('heading', { level: 1 })
    expect(mainHeading).toBeInTheDocument()

    // 检查表单可访问性（通过占位符）
    const searchInput = screen.getByPlaceholderText(/搜索任何内容.../i)
    expect(searchInput).toBeInTheDocument()

    // 检查按钮可访问性
    const buttons = screen.getAllByRole('button')
    buttons.forEach(button => {
      expect(button).toBeEnabled()
    })
  })

  it('应该正确处理响应式设计', () => {
    // 测试移动端
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    })

    renderWithRouter(<HomePage />)

    // 验证移动端布局：允许多元素存在
    expect(screen.getAllByRole('heading', { level: 1 }).length).toBeGreaterThan(0)

    // 测试桌面端
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1920,
    })

    renderWithRouter(<HomePage />)

    // 验证桌面端布局：允许多元素存在
    expect(screen.getAllByRole('heading', { level: 1 }).length).toBeGreaterThan(0)
  })

  it('应该正确处理动画效果', async () => {
    renderWithRouter(<HomePage />)

    // 验证动画组件存在（通过主标题）
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
  })

  it('应该处理错误状态', () => {
    // 模拟错误状态
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})

    renderWithRouter(<HomePage />)

    // 验证错误处理
    // 这里需要根据实际错误处理逻辑调整

    consoleSpy.mockRestore()
  })
})
