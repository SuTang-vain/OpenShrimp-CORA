import * as React from 'react'
import { Link, useLocation } from 'react-router-dom'
// import { motion } from 'framer-motion'
import {
  Home,
  Search,
  FileText,
  Settings,
  BarChart3,
  BookOpen,
  Upload,
  History,
  Star,
  Tag,
  ChevronLeft,
  ChevronRight,
  Cog,
  Network,
} from 'lucide-react'

import { useAuth } from '@/stores/authStore'
import { cn } from '@/utils/cn'
import logo from '@/assets/Open-Shrimp.jpg'

/**
 * 侧边栏组件属性
 */
interface SidebarProps {
  collapsed?: boolean
  onToggleCollapse?: () => void
  onClose?: () => void
  className?: string
}

/**
 * 导航项接口
 */
interface NavItem {
  id: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  href: string
  badge?: string | number
  requireAuth?: boolean
  children?: NavItem[]
}

/**
 * 导航配置
 */
const navigationItems: NavItem[] = [
  {
    id: 'home',
    label: '首页',
    icon: Home,
    href: '/',
  },
  {
    id: 'search',
    label: '智能搜索',
    icon: Search,
    href: '/search',
  },
  {
    id: 'graph',
    label: '图谱工作台',
    icon: Network,
    href: '/graph',
    requireAuth: true,
  },
  {
    id: 'documents',
    label: '文档管理',
    icon: FileText,
    href: '/documents',
    requireAuth: true,
    children: [
      {
        id: 'documents-all',
        label: '所有文档',
        icon: BookOpen,
        href: '/documents',
      },
      {
        id: 'documents-upload',
        label: '上传文档',
        icon: Upload,
        href: '/documents/upload',
      },
      {
        id: 'documents-favorites',
        label: '收藏文档',
        icon: Star,
        href: '/documents/favorites',
      },
      {
        id: 'documents-tags',
        label: '标签管理',
        icon: Tag,
        href: '/documents/tags',
      },
    ],
  },
  {
    id: 'history',
    label: '搜索历史',
    icon: History,
    href: '/history',
    requireAuth: true,
  },
  {
    id: 'analytics',
    label: '数据分析',
    icon: BarChart3,
    href: '/analytics',
    requireAuth: true,
  },
  {
    id: 'services',
    label: '服务配置',
    icon: Cog,
    href: '/services',
    requireAuth: true,
  },
  {
    id: 'settings',
    label: '设置',
    icon: Settings,
    href: '/settings',
    requireAuth: true,
  },
]

/**
 * 侧边栏组件
 * 提供应用的主要导航功能
 */
const Sidebar: React.FC<SidebarProps> = ({
  collapsed = false,
  onToggleCollapse,
  onClose,
  className,
}) => {
  const location = useLocation()
  const { isAuthenticated } = useAuth()

  /**
   * 检查路径是否激活
   */
  const isPathActive = (href: string): boolean => {
    if (href === '/') {
      return location.pathname === '/'
    }
    return location.pathname.startsWith(href)
  }

  /**
   * 过滤导航项（根据认证状态）
   */
  const getFilteredNavItems = (items: NavItem[]): NavItem[] => {
    return items.filter(item => {
      if (item.requireAuth && !isAuthenticated) {
        return false
      }
      return true
    })
  }

  /**
   * 渲染导航项
   */
  const renderNavItem = (item: NavItem, level: number = 0) => {
    const isActive = isPathActive(item.href)
    const hasChildren = item.children && item.children.length > 0
    const Icon = item.icon

    return (
      <div key={item.id}>
        <Link
          to={item.href}
          onClick={onClose}
          className={cn(
            'flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
            'hover:bg-accent hover:text-accent-foreground',
            isActive && 'bg-primary text-primary-foreground hover:bg-primary/90',
            collapsed && 'justify-center px-2',
            level > 0 && 'ml-6 text-xs'
          )}
          title={collapsed ? item.label : undefined}
        >
          <Icon className={cn('h-5 w-5 flex-shrink-0', level > 0 && 'h-4 w-4')} />
          
          {!collapsed && (
            <>
              <span className="flex-1">{item.label}</span>
              {item.badge && (
                <span className="badge badge-secondary text-xs">
                  {item.badge}
                </span>
              )}
            </>
          )}
        </Link>

        {/* 子导航项 */}
        {hasChildren && !collapsed && (
          <div className="mt-1 space-y-1">
            {item.children!.map(child => renderNavItem(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  const filteredNavItems = getFilteredNavItems(navigationItems)

  return (
    <aside
      className={cn(
        'bg-card border-r flex flex-col h-full',
        collapsed ? 'w-16' : 'w-64',
        className
      )}
    >
      {/* 侧边栏头部 */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          {!collapsed && (
            <h2 className="text-lg font-semibold text-card-foreground">
              导航菜单
            </h2>
          )}
          
          {onToggleCollapse && (
            <button
              onClick={onToggleCollapse}
              className="btn btn-ghost btn-sm"
              aria-label={collapsed ? '展开侧边栏' : '折叠侧边栏'}
            >
              {collapsed ? (
                <ChevronRight className="h-4 w-4" />
              ) : (
                <ChevronLeft className="h-4 w-4" />
              )}
            </button>
          )}
        </div>
      </div>

      {/* 导航列表 */}
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto scrollbar-hide">
        {filteredNavItems.map(item => renderNavItem(item))}
      </nav>

      {/* 侧边栏底部 */}
      <div className="p-4 border-t">
        {!collapsed && (
          <div className="text-xs text-muted-foreground space-y-1">
        <p>CORA v2.0.0</p>
            <p>© 2024 Shrimp Team</p>
          </div>
        )}
        
        {collapsed && (
          <div className="flex justify-center">
            <img src={logo} alt="OpenShrimp" className="w-8 h-8 rounded-lg object-contain" />
          </div>
        )}
      </div>
    </aside>
  )
}

export default Sidebar