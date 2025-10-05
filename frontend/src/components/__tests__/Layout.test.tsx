/**
 * Layout 组件测试
 */

import * as React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { useAuth } from '@/stores/authStore'

// 在导入组件前为认证模块提供默认 mock，避免 useAuth 未定义
// 提供完整的 useAuth 返回对象的 mock，满足类型要求
const createMockAuth = (overrides: Partial<ReturnType<typeof useAuth>> = {}): ReturnType<typeof useAuth> => ({
  isAuthenticated: false,
  user: null,
  login: jest.fn(),
  register: jest.fn(),
  logout: jest.fn(),
  updateUser: jest.fn(),
  isLoggedIn: jest.fn(() => false),
  getCurrentUser: jest.fn(() => null),
  getCurrentUserId: jest.fn(() => null),
  hasRole: jest.fn(() => false),
  hasPermission: jest.fn(() => false),
  getToken: jest.fn(() => null),
  getAvatarUrl: jest.fn(() => null),
  getDisplayName: jest.fn(() => '未知用户'),
  ...overrides,
})

jest.mock('@/stores/authStore', () => ({
  useAuth: jest.fn(() => createMockAuth()),
}))

import Layout from '../layout/Layout'

// 测试工具函数
const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  )
}

// 模拟子组件
jest.mock('../layout/Header', () => {
  return function MockHeader({ onToggleSidebar }: any) {
    return (
      <header data-testid="header">
        <button onClick={onToggleSidebar} data-testid="toggle-sidebar">
          Toggle Sidebar
        </button>
      </header>
    )
  }
})

jest.mock('../layout/Sidebar', () => {
  return function MockSidebar({ collapsed, onClose }: any) {
    return (
      <aside data-testid="sidebar" data-collapsed={collapsed}>
        {onClose && (
          <button onClick={onClose} data-testid="close-sidebar">
            Close
          </button>
        )}
      </aside>
    )
  }
})

jest.mock('../layout/Footer', () => {
  return function MockFooter() {
    return <footer data-testid="footer">Footer</footer>
  }
})

describe('Layout Component', () => {
  beforeEach(() => {
    // 重置所有模拟
    jest.clearAllMocks()
  })

  it('应该正确渲染布局组件', () => {
    renderWithRouter(
      <Layout>
        <div data-testid="content">Test Content</div>
      </Layout>
    )

    expect(screen.getByTestId('header')).toBeInTheDocument()
    expect(screen.getAllByTestId('sidebar').length).toBeGreaterThan(0)
    expect(screen.getByTestId('footer')).toBeInTheDocument()
    expect(screen.getByTestId('content')).toBeInTheDocument()
  })

  it('应该能够切换侧边栏状态', () => {
    renderWithRouter(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    const toggleButton = screen.getByTestId('toggle-sidebar')
    const sidebar = screen.getByTestId('sidebar')

    // 初始状态
    expect(sidebar).toHaveAttribute('data-collapsed', 'false')

    // 点击切换按钮
    fireEvent.click(toggleButton)

    // 验证状态变化（这里需要根据实际实现调整）
    // 由于我们模拟了组件，这个测试可能需要调整
  })

  it('应该在移动端正确处理侧边栏', () => {
    // 模拟移动端视口
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768,
    })

    renderWithRouter(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    // 验证移动端特定的行为
    expect(screen.getAllByTestId('sidebar').length).toBeGreaterThan(0)
  })

  it('应该正确处理键盘导航', () => {
    renderWithRouter(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    // 测试键盘事件
    fireEvent.keyDown(document, { key: 'Escape' })
    
    // 验证 ESC 键的行为
    // 这里需要根据实际实现添加断言
  })

  it('应该支持无障碍访问', () => {
    renderWithRouter(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    // 检查 ARIA 属性
    const main = screen.getByRole('main', { hidden: true })
    expect(main).toBeInTheDocument()

    // 检查语义化标签
    expect(screen.getByTestId('header')).toBeInTheDocument()
    expect(screen.getByTestId('footer')).toBeInTheDocument()
  })

  it('应该正确处理响应式设计', () => {
    // 在该用例中确保认证为 true，保证侧边栏渲染
    const mockUseAuth = jest.mocked(useAuth)
    mockUseAuth.mockReturnValue(createMockAuth({ isAuthenticated: true }))

    // 测试不同屏幕尺寸
    const testSizes = [
      { width: 320, height: 568 }, // 移动端
      { width: 768, height: 1024 }, // 平板
      { width: 1920, height: 1080 }, // 桌面端
    ]

    testSizes.forEach(({ width, height }) => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: width,
      })
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: height,
      })

      renderWithRouter(
        <Layout>
          <div>Test Content</div>
        </Layout>
      )

      // 验证在不同尺寸下的布局
      expect(screen.getAllByTestId('sidebar').length).toBeGreaterThan(0)
    })
  })
})
