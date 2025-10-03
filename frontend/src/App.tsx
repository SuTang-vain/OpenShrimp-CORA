import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
// import { motion, AnimatePresence } from 'framer-motion'

// 页面组件
import Layout from '@/components/layout/Layout'
import HomePage from '@/pages/HomePage'
import SearchPage from '@/pages/SearchPage'
import DocumentsPage from '@/pages/DocumentsPage'
import SettingsPage from '@/pages/SettingsPage'
import ServiceConfigurationPage from '@/pages/ServiceConfigurationPage'
import RegisterPage from '@/pages/RegisterPage'
import NotFoundPage from '@/pages/NotFoundPage'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'

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

  // 页面过渡动画配置
  const pageVariants = {
    initial: {
      opacity: 0,
      y: 20,
    },
    in: {
      opacity: 1,
      y: 0,
    },
    out: {
      opacity: 0,
      y: -20,
    },
  }

  const pageTransition = {
    type: 'tween',
    ease: 'anticipate',
    duration: 0.3,
  }

  return (
    <div className={cn('min-h-screen bg-background text-foreground', theme)}>
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

          {/* 控制台页面（需鉴权） */}
          <Route path="/dashboard" element={<DashboardPage />} />

          {/* 404 页面 */}
          <Route path="/404" element={<NotFoundPage />} />

          {/* 重定向到 404 */}
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Route>

        {/* 认证页面不使用 Layout */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Routes>
    </div>
  )
}

export default App