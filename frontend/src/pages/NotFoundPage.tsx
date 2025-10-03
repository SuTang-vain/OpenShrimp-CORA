import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
// import { motion } from 'framer-motion'
import {
  Home,
  Search,
  ArrowLeft,
  FileQuestion,
  Compass,
} from 'lucide-react'

/**
 * 404 页面组件
 * 当用户访问不存在的页面时显示
 */
const NotFoundPage: React.FC = () => {
  const navigate = useNavigate()

  /**
   * 返回上一页
   */
  const goBack = () => {
    if (window.history.length > 1) {
      navigate(-1)
    } else {
      navigate('/')
    }
  }



  return (
    <div className="min-h-[80vh] flex items-center justify-center">
      <div className="text-center max-w-2xl mx-auto px-4">
        <div className="space-y-8">
          {/* 404 图标和数字 */}
          <div className="relative">
            <div className="inline-flex items-center justify-center w-32 h-32 bg-primary/10 rounded-full mb-6">
              <FileQuestion className="h-16 w-16 text-primary" />
            </div>
            
            <div className="text-8xl lg:text-9xl font-bold text-primary/20 select-none">
              404
            </div>
          </div>

          {/* 错误信息 */}
          <div className="space-y-4">
            <h1 className="text-3xl lg:text-4xl font-bold text-foreground">
              页面未找到
            </h1>
            <p className="text-lg text-muted-foreground max-w-md mx-auto">
              抱歉，您访问的页面不存在或已被移动。请检查URL是否正确，或返回首页继续浏览。
            </p>
          </div>

          {/* 操作按钮 */}
          <div className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-4">
            <Link
              to="/"
              className="btn btn-primary btn-lg"
            >
              <Home className="h-5 w-5 mr-2" />
              返回首页
            </Link>
            
            <button
              onClick={goBack}
              className="btn btn-outline btn-lg"
            >
              <ArrowLeft className="h-5 w-5 mr-2" />
              返回上页
            </button>
          </div>

          {/* 快速导航 */}
          <div className="pt-8">
            <p className="text-sm text-muted-foreground mb-4">
              或者您可以访问以下页面：
            </p>
            
            <div className="flex flex-wrap items-center justify-center gap-4">
              <Link
                to="/search"
                className="inline-flex items-center space-x-2 text-primary hover:text-primary/80 transition-colors"
              >
                <Search className="h-4 w-4" />
                <span>智能搜索</span>
              </Link>
              
              <span className="text-muted-foreground">•</span>
              
              <Link
                to="/documents"
                className="inline-flex items-center space-x-2 text-primary hover:text-primary/80 transition-colors"
              >
                <Compass className="h-4 w-4" />
                <span>文档管理</span>
              </Link>
            </div>
          </div>

          {/* 装饰性元素 */}
          <div className="pt-8 opacity-50">
            <div className="flex items-center justify-center space-x-2 text-xs text-muted-foreground">
              <span>错误代码: 404</span>
              <span>•</span>
              <span>页面不存在</span>
            </div>
          </div>
        </div>
      </div>

      {/* 背景装饰 */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-secondary/5 rounded-full blur-3xl" />
        <div className="absolute top-3/4 left-3/4 w-48 h-48 bg-accent/5 rounded-full blur-3xl" />
      </div>
    </div>
  )
}

export default NotFoundPage