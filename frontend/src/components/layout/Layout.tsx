import React, { useState } from 'react'
import { Outlet } from 'react-router-dom'
// import { motion, AnimatePresence } from 'framer-motion'

import Header from './Header'
import Sidebar from './Sidebar'
import Footer from './Footer'
import { cn } from '@/utils/cn'

/**
 * 布局组件属性
 */
interface LayoutProps {
  children?: React.ReactNode
}

/**
 * 主布局组件
 * 提供应用的整体布局结构，包括头部、侧边栏、主内容区域和底部
 */
const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  /**
   * 切换侧边栏开关状态
   */
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen)
  }

  /**
   * 切换侧边栏折叠状态
   */
  const toggleSidebarCollapse = () => {
    setSidebarCollapsed(!sidebarCollapsed)
  }

  /**
   * 关闭侧边栏
   */
  const closeSidebar = () => {
    setSidebarOpen(false)
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* 头部导航 */}
      <Header
        onToggleSidebar={toggleSidebar}
        onToggleSidebarCollapse={toggleSidebarCollapse}
        sidebarOpen={sidebarOpen}
        sidebarCollapsed={sidebarCollapsed}
      />

      <div className="flex flex-1 relative">
        {/* 侧边栏 */}
        {/* 桌面端侧边栏 */}
        <div
          className={cn(
            "hidden lg:block relative z-10 transition-all duration-300 ease-in-out",
            sidebarCollapsed ? "w-16" : "w-64"
          )}
        >
          <Sidebar
            collapsed={sidebarCollapsed}
            onToggleCollapse={toggleSidebarCollapse}
            className="h-full"
          />
        </div>

        {/* 移动端侧边栏遮罩 */}
        {sidebarOpen && (
          <div
            className="lg:hidden fixed inset-0 bg-black/50 z-40"
            onClick={closeSidebar}
          />
        )}

        {/* 移动端侧边栏 */}
        {sidebarOpen && (
          <div className="lg:hidden fixed left-0 top-16 bottom-0 w-64 z-50">
            <Sidebar
              collapsed={false}
              onClose={closeSidebar}
              className="h-full"
            />
          </div>
        )}

        {/* 主内容区域 */}
        <main
          className={cn(
            'flex-1 flex flex-col min-h-0',
            'transition-all duration-300 ease-in-out'
          )}
        >
          {/* 内容容器 */}
          <div className="flex-1 overflow-auto">
            <div className="container-responsive py-6">
              {/* 页面内容 */}
              <div className="min-h-full">
                {children || <Outlet />}
              </div>
            </div>
          </div>

          {/* 底部 */}
          <Footer />
        </main>
      </div>

      {/* 全局快捷键提示 */}
      <div className="sr-only">
        <div aria-live="polite" aria-atomic="true">
          按 Ctrl+K 打开搜索
        </div>
      </div>
    </div>
  )
}

export default Layout