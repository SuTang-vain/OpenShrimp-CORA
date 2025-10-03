import * as React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { HelmetProvider } from 'react-helmet-async'
import { Toaster } from 'sonner'

import App from './App.tsx'
import './index.css'

// 错误边界组件
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('应用错误:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-background">
          <div className="text-center space-y-4">
            <h1 className="text-2xl font-bold text-destructive">应用出现错误</h1>
            <p className="text-muted-foreground">
              {this.state.error?.message || '未知错误'}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="btn btn-primary btn-md"
            >
              重新加载
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

// 性能监控
if ((import.meta as any).env.PROD) {
  // 监控页面加载性能
  window.addEventListener('load', () => {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
    const loadTime = navigation.loadEventEnd - navigation.loadEventStart
    // eslint-disable-next-line no-console
    console.log(`页面加载时间: ${loadTime}ms`)
  })
}

// 应用启动函数
const startApp = async () => {
  try {
    // 应用初始化逻辑
    // eslint-disable-next-line no-console
    console.log('应用启动中...')
  } catch (error) {
    console.error('应用启动失败:', error)
  }
}

startApp()

// 开发环境下的调试工具
if ((import.meta as any).env.DEV) {
  // 添加全局调试对象
  // eslint-disable-next-line no-extra-semi
  ;(window as any).__SHRIMP_DEBUG__ = {
    version: '2.0.0',
    env: (import.meta as any).env,
    performance: performance,
  }
  // 开发环境下的性能监控
  const perf = window.performance as any
  window.performance = {
    ...window.performance,
    mark: window.performance?.mark || (() => {}),
    measure: window.performance?.measure || (() => {}),
    getEntriesByType: window.performance?.getEntriesByType || (() => []),
    now: window.performance?.now || Date.now,
    timing: window.performance?.timing || {},
    navigation: window.performance?.navigation || {},
    ...(perf?.memory && { memory: perf.memory }),
  }
  // 开发环境下的性能监控
  // window.__REACT_DEVTOOLS_GLOBAL_HOOK__ = window.__REACT_DEVTOOLS_GLOBAL_HOOK__ || {}
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <HelmetProvider>
        <BrowserRouter>
          <App />
          <Toaster
            position="top-right"
            expand={false}
            richColors
            closeButton
            toastOptions={{
              duration: 4000,
              style: {
                background: 'hsl(var(--card))',
                color: 'hsl(var(--card-foreground))',
                border: '1px solid hsl(var(--border))',
              },
            }}
          />
        </BrowserRouter>
      </HelmetProvider>
    </ErrorBoundary>
  </React.StrictMode>
)