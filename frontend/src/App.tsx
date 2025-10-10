import { useEffect, lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'

// 页面组件（按需加载）
const Layout = lazy(() => import('@/components/layout/Layout'))
const HomePage = lazy(() => import('@/pages/HomePage'))
const SearchPage = lazy(() => import('@/pages/SearchPage'))
const DocumentsPage = lazy(() => import('@/pages/DocumentsPage'))
const SettingsPage = lazy(() => import('@/pages/SettingsPage'))
const ServiceConfigurationPage = lazy(() => import('@/pages/ServiceConfigurationPage'))
const RegisterPage = lazy(() => import('@/pages/RegisterPage'))
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'))
const LoginPage = lazy(() => import('@/pages/LoginPage'))
const DashboardPage = lazy(() => import('@/pages/DashboardPage'))
const GraphWorkbenchPage = lazy(() => import('@/pages/GraphWorkbenchPage'))
const ToolsConsolePage = lazy(() => import('@/pages/ToolsConsolePage'))
const OrchestratorPage = lazy(() => import('@/pages/OrchestratorPage'))
const GraphWorkspacePage = lazy(() => import('@/pages/GraphWorkspacePage'))

// Hooks
import { useThemeStore } from '@/stores/themeStore'
import { useAuthStore } from '@/stores/authStore'

// 工具函数
import { cn } from '@/utils/cn'

/**
 * 主应用组件
 * 负责路由配置、主题管理和全局状态初始化
 */
function App() {
  const { theme, initializeTheme } = useThemeStore()
  const { initializeAuth } = useAuthStore()

  // 初始化应用
  useEffect(() => {
    const initApp = async () => {
      try {
        // 初始化主题
        initializeTheme()
        
        // 初始化认证状态
        await initializeAuth()
        
        // eslint-disable-next-line no-console
        console.log('应用初始化完成')
      } catch (error) {
        console.error('应用初始化失败:', error)
      }
    }

    initApp()
  }, [initializeAuth, initializeTheme])

  // 已移除未使用的页面过渡动画配置，避免 TS6133 未使用变量错误

  return (
    <div className={cn('min-h-screen bg-background text-foreground', theme)}>
      <Suspense fallback={<div className="p-8 text-center text-sm text-muted-foreground">页面加载中...</div>}>
      <Routes>
        {/* 使用 Layout 的业务路由 */}
        <Route element={<Layout />}>
          {/* 首页 */}
          <Route path="/" element={<HomePage />} />

          {/* 搜索页面 */}
          <Route path="/search" element={<SearchPage />} />

          {/* 文档管理页面 */}
          <Route path="/documents" element={<DocumentsPage />} />

          {/* 设置页面 */}
          <Route path="/settings" element={<SettingsPage />} />

          {/* 服务配置页面 */}
          <Route path="/services" element={<ServiceConfigurationPage />} />

          {/* Strata 工具控制台 */}
          <Route path="/tools" element={<ToolsConsolePage />} />

          {/* Orchestrator 控制台页面 */}
          <Route path="/orchestrator" element={<OrchestratorPage />} />

          {/* 控制台页面（需鉴权） */}
          <Route path="/dashboard" element={<DashboardPage />} />

          {/* 图谱工作台页面（完整工作台） */}
          <Route path="/graph" element={<GraphWorkbenchPage />} />
          {/* 最小工作台保留在 /graph/min */}
          <Route path="/graph/min" element={<GraphWorkspacePage />} />

          {/* 404 页面 */}
          <Route path="/404" element={<NotFoundPage />} />

          {/* 重定向到 404 */}
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Route>

        {/* 认证页面不使用 Layout */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Routes>
      </Suspense>
    </div>
  )
}

export default App