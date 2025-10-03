import * as React from 'react'
import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
// import { motion, AnimatePresence } from 'framer-motion'
import {
  Menu,
  Search,
  Bell,
  Settings,
  User,
  LogOut,
  Moon,
  Sun,
  Monitor,
  ChevronDown,
  Command,
} from 'lucide-react'

import { useAuth } from '@/stores/authStore'
import { useThemeStore } from '@/stores/themeStore'
import { cn } from '@/utils/cn'
import logo from '@/assets/OpenShrimp.jpg'

/**
 * 头部组件属性
 */
interface HeaderProps {
  onToggleSidebar: () => void
  onToggleSidebarCollapse: () => void
  sidebarOpen: boolean
  sidebarCollapsed: boolean
}

/**
 * 头部导航组件
 * 包含logo、搜索框、用户菜单、主题切换等功能
 */
const Header: React.FC<HeaderProps> = ({
  onToggleSidebar,
  onToggleSidebarCollapse,
  sidebarOpen: _sidebarOpen,
  sidebarCollapsed: _sidebarCollapsed,
}) => {
  const navigate = useNavigate()
  const { isAuthenticated, user, logout } = useAuth()
  const { theme, setTheme } = useThemeStore()
  
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [themeMenuOpen, setThemeMenuOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchFocused, setSearchFocused] = useState(false)
  
  const userMenuRef = useRef<HTMLDivElement>(null)
  const themeMenuRef = useRef<HTMLDivElement>(null)
  const searchRef = useRef<HTMLInputElement>(null)

  // 点击外部关闭菜单
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false)
      }
      if (themeMenuRef.current && !themeMenuRef.current.contains(event.target as Node)) {
        setThemeMenuOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // 全局快捷键
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ctrl+K 或 Cmd+K 聚焦搜索框
      if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault()
        searchRef.current?.focus()
      }
      
      // ESC 取消搜索焦点
      if (event.key === 'Escape' && searchFocused) {
        searchRef.current?.blur()
        setSearchQuery('')
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [searchFocused])

  /**
   * 处理搜索提交
   */
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`)
      searchRef.current?.blur()
    }
  }

  /**
   * 处理用户登出
   */
  const handleLogout = async () => {
    try {
      await logout()
      navigate('/login')
    } catch (error) {
      console.error('登出失败:', error)
    }
  }

  /**
   * 主题图标
   */
  const ThemeIcon = () => {
    switch (theme) {
      case 'light':
        return <Sun className="h-4 w-4" />
      case 'dark':
        return <Moon className="h-4 w-4" />
      default:
        return <Monitor className="h-4 w-4" />
    }
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container-responsive">
        <div className="flex h-16 items-center justify-between">
          {/* 左侧：Logo 和导航 */}
          <div className="flex items-center space-x-4">
            {/* 移动端菜单按钮 */}
            <button
              onClick={onToggleSidebar}
              className="lg:hidden btn btn-ghost btn-sm"
              aria-label="切换菜单"
            >
              <Menu className="h-5 w-5" />
            </button>

            {/* 桌面端侧边栏切换 */}
            <button
              onClick={onToggleSidebarCollapse}
              className="hidden lg:flex btn btn-ghost btn-sm"
              aria-label="切换侧边栏"
            >
              <Menu className="h-5 w-5" />
            </button>

            {/* Logo */}
            <Link
              to="/"
              className="flex items-center space-x-2 font-bold text-xl text-gradient"
            >
              <img src={logo} alt="OpenShrimp" className="w-8 h-8 rounded-lg object-contain" />
              <span className="hidden sm:block">Shrimp Agent</span>
            </Link
            >
          </div>

          {/* 中间：搜索框 */}
          <div className="flex-1 max-w-md mx-4">
            <form onSubmit={handleSearchSubmit} className="relative">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  ref={searchRef}
                  type="text"
                  placeholder="搜索文档和内容..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onFocus={() => setSearchFocused(true)}
                  onBlur={() => setSearchFocused(false)}
                  className={cn(
                    'input pl-10 pr-16 w-full',
                    searchFocused && 'ring-2 ring-primary'
                  )}
                />
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
                  <kbd className="hidden sm:inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
                    <Command className="h-3 w-3" />
                    K
                  </kbd>
                </div>
              </div>
            </form>
          </div>

          {/* 右侧：用户操作 */}
          <div className="flex items-center space-x-2">
            {/* 通知按钮 */}
            {isAuthenticated && (
              <button
                className="btn btn-ghost btn-sm relative"
                aria-label="通知"
              >
                <Bell className="h-5 w-5" />
                {/* 通知徽章 */}
                <span className="absolute -top-1 -right-1 h-3 w-3 bg-destructive rounded-full text-[10px] text-destructive-foreground flex items-center justify-center">
                  3
                </span>
              </button>
            )}

            {/* 主题切换 */}
            <div className="relative" ref={themeMenuRef}>
              <button
                onClick={() => setThemeMenuOpen(!themeMenuOpen)}
                className="btn btn-ghost btn-sm"
                aria-label="切换主题"
              >
                <ThemeIcon />
              </button>

              {themeMenuOpen && (
                <div className="absolute right-0 top-full mt-2 w-48 bg-popover border rounded-md shadow-lg z-50">
                    <div className="py-1">
                      <button
                        onClick={() => {
                          setTheme('light')
                          setThemeMenuOpen(false)
                        }}
                        className={cn(
                          'w-full px-4 py-2 text-left text-sm hover:bg-accent flex items-center space-x-2',
                          theme === 'light' && 'bg-accent'
                        )}
                      >
                        <Sun className="h-4 w-4" />
                        <span>浅色模式</span>
                      </button>
                      <button
                        onClick={() => {
                          setTheme('dark')
                          setThemeMenuOpen(false)
                        }}
                        className={cn(
                          'w-full px-4 py-2 text-left text-sm hover:bg-accent flex items-center space-x-2',
                          theme === 'dark' && 'bg-accent'
                        )}
                      >
                        <Moon className="h-4 w-4" />
                        <span>深色模式</span>
                      </button>
                      <button
                        onClick={() => {
                          setTheme('system')
                          setThemeMenuOpen(false)
                        }}
                        className={cn(
                          'w-full px-4 py-2 text-left text-sm hover:bg-accent flex items-center space-x-2',
                          theme === 'system' && 'bg-accent'
                        )}
                      >
                        <Monitor className="h-4 w-4" />
                        <span>跟随系统</span>
                      </button>
                    </div>
                </div>
              )}
            </div>

            {/* 用户菜单 */}
            {isAuthenticated ? (
              <div className="relative" ref={userMenuRef}>
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center space-x-2 btn btn-ghost btn-sm"
                >
                  <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                    {user?.avatar ? (
                      <img
                        src={user.avatar}
                        alt={user.username}
                        className="w-full h-full rounded-full object-cover"
                      />
                    ) : (
                      <User className="h-4 w-4 text-primary-foreground" />
                    )}
                  </div>
                  <span className="hidden sm:block text-sm font-medium">
                    {user?.username || '用户'}
                  </span>
                  <ChevronDown className="h-4 w-4" />
                </button>

                {userMenuOpen && (
                  <div className="absolute right-0 top-full mt-2 w-56 bg-popover border rounded-md shadow-lg z-50">
                      <div className="py-1">
                        <div className="px-4 py-2 border-b">
                          <p className="text-sm font-medium">{user?.username}</p>
                          <p className="text-xs text-muted-foreground">{user?.email}</p>
                        </div>
                        
                        <Link
                          to="/settings"
                          onClick={() => setUserMenuOpen(false)}
                          className="w-full px-4 py-2 text-left text-sm hover:bg-accent flex items-center space-x-2"
                        >
                          <Settings className="h-4 w-4" />
                          <span>设置</span>
                        </Link>
                        
                        <button
                          onClick={() => {
                            handleLogout()
                            setUserMenuOpen(false)
                          }}
                          className="w-full px-4 py-2 text-left text-sm hover:bg-accent flex items-center space-x-2 text-destructive"
                        >
                          <LogOut className="h-4 w-4" />
                          <span>退出登录</span>
                        </button>
                      </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Link
                  to="/login"
                  className="btn btn-ghost btn-sm"
                >
                  登录
                </Link>
                <Link
                  to="/register"
                  className="btn btn-primary btn-sm"
                >
                  注册
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header