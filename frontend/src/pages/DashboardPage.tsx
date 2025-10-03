import * as React from 'react'
import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { BarChart3, Settings, FileText, Search, User as UserIcon } from 'lucide-react'

import { useAuth } from '@/stores/authStore'
import { cn } from '@/utils/cn'

const DashboardPage: React.FC = () => {
  const navigate = useNavigate()
  const { isAuthenticated, user, getDisplayName } = useAuth()

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { replace: true })
    }
  }, [isAuthenticated, navigate])

  const displayName = getDisplayName()

  return (
    <div className={cn('min-h-[80vh]')}> 
      {/* 顶部欢迎区 */}
      <div className="bg-card border rounded-xl p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">控制台</h1>
            <p className="text-muted-foreground mt-1">
              欢迎回来，{displayName || user?.username || '用户'}
            </p>
          </div>
          <div className="hidden sm:flex items-center space-x-2 text-muted-foreground">
            <UserIcon className="h-5 w-5" />
            <span className="text-sm">{user?.email || '未绑定邮箱'}</span>
          </div>
        </div>
      </div>

      {/* 功能快捷入口 */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {/* 服务配置 */}
        <Link to="/services" className="group block bg-card border rounded-xl p-5 hover:border-primary transition-colors">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Settings className="h-6 w-6 text-primary" />
              <div>
                <h2 className="text-lg font-semibold">服务配置</h2>
                <p className="text-sm text-muted-foreground">管理 AI 模型与检索服务</p>
              </div>
            </div>
            <span className="text-xs text-muted-foreground group-hover:text-primary">前往</span>
          </div>
        </Link>

        {/* 文档管理 */}
        <Link to="/documents" className="group block bg-card border rounded-xl p-5 hover:border-primary transition-colors">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileText className="h-6 w-6 text-primary" />
              <div>
                <h2 className="text-lg font-semibold">文档管理</h2>
                <p className="text-sm text-muted-foreground">上传、处理与管理文档</p>
              </div>
            </div>
            <span className="text-xs text-muted-foreground group-hover:text-primary">前往</span>
          </div>
        </Link>

        {/* 智能搜索 */}
        <Link to="/search" className="group block bg-card border rounded-xl p-5 hover:border-primary transition-colors">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Search className="h-6 w-6 text-primary" />
              <div>
                <h2 className="text-lg font-semibold">智能搜索</h2>
                <p className="text-sm text-muted-foreground">基于AI的高效检索</p>
              </div>
            </div>
            <span className="text-xs text-muted-foreground group-hover:text-primary">前往</span>
          </div>
        </Link>

        {/* 统计概览 */}
        <div className="bg-card border rounded-xl p-5">
          <div className="flex items-center space-x-3 mb-4">
            <BarChart3 className="h-6 w-6 text-primary" />
            <h2 className="text-lg font-semibold">使用概览</h2>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-muted/30">
              <p className="text-sm text-muted-foreground">文档数量</p>
              <p className="text-xl font-bold">—</p>
            </div>
            <div className="p-4 rounded-lg bg-muted/30">
              <p className="text-sm text-muted-foreground">搜索次数</p>
              <p className="text-xl font-bold">—</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DashboardPage