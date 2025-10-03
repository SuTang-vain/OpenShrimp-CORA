import * as React from 'react'
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import type { Theme } from '@/types'

/**
 * 主题状态接口
 */
interface ThemeState {
  theme: Theme
  systemTheme: 'light' | 'dark'
  resolvedTheme: 'light' | 'dark'
}

/**
 * 主题操作接口
 */
interface ThemeActions {
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
  initializeTheme: () => void
  updateSystemTheme: (systemTheme: 'light' | 'dark') => void
}

/**
 * 主题状态管理
 */
export const useThemeStore = create<ThemeState & ThemeActions>()(
  persist(
    (set, get) => ({
      // 初始状态
      theme: 'system',
      systemTheme: 'light',
      resolvedTheme: 'light',

      // 设置主题
      setTheme: (theme: Theme) => {
        set({ theme })
        
        const { systemTheme } = get()
        const resolvedTheme = theme === 'system' ? systemTheme : theme
        
        set({ resolvedTheme })
        applyTheme(resolvedTheme)
      },

      // 切换主题
      toggleTheme: () => {
        const { theme } = get()
        
        if (theme === 'system') {
          set({ theme: 'light' })
          set({ resolvedTheme: 'light' })
          applyTheme('light')
        } else if (theme === 'light') {
          set({ theme: 'dark' })
          set({ resolvedTheme: 'dark' })
          applyTheme('dark')
        } else {
          set({ theme: 'system' })
          const { systemTheme } = get()
          set({ resolvedTheme: systemTheme })
          applyTheme(systemTheme)
        }
      },

      // 初始化主题
      initializeTheme: () => {
        // 检测系统主题
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
          ? 'dark'
          : 'light'
        
        set({ systemTheme })
        
        const { theme } = get()
        const resolvedTheme = theme === 'system' ? systemTheme : theme
        
        set({ resolvedTheme })
        applyTheme(resolvedTheme)
        
        // 监听系统主题变化
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
        const handleChange = (e: MediaQueryListEvent) => {
          const newSystemTheme = e.matches ? 'dark' : 'light'
          get().updateSystemTheme(newSystemTheme)
        }
        
        mediaQuery.addEventListener('change', handleChange)
        
        // 返回清理函数
        return () => {
          mediaQuery.removeEventListener('change', handleChange)
        }
      },

      // 更新系统主题
      updateSystemTheme: (systemTheme: 'light' | 'dark') => {
        set({ systemTheme })
        
        const { theme } = get()
        if (theme === 'system') {
          set({ resolvedTheme: systemTheme })
          applyTheme(systemTheme)
        }
      },
    }),
    {
      name: 'shrimp-theme-storage',
      partialize: (state) => ({ theme: state.theme }),
    }
  )
)

/**
 * 应用主题到 DOM
 */
function applyTheme(theme: 'light' | 'dark') {
  const root = document.documentElement
  
  // 移除之前的主题类
  root.classList.remove('light', 'dark')
  
  // 添加新的主题类
  root.classList.add(theme)
  
  // 更新 meta 标签
  updateMetaThemeColor(theme)
  
  // 触发自定义事件
  window.dispatchEvent(
    new CustomEvent('theme-changed', {
      detail: { theme },
    })
  )
}

/**
 * 更新 meta 主题颜色
 */
function updateMetaThemeColor(theme: 'light' | 'dark') {
  const metaThemeColor = document.querySelector('meta[name="theme-color"]')
  
  if (metaThemeColor) {
    const color = theme === 'dark' ? '#0f172a' : '#ffffff'
    metaThemeColor.setAttribute('content', color)
  } else {
    // 如果不存在，创建一个
    const meta = document.createElement('meta')
    meta.name = 'theme-color'
    meta.content = theme === 'dark' ? '#0f172a' : '#ffffff'
    document.head.appendChild(meta)
  }
}

/**
 * 获取当前解析的主题
 */
export const getResolvedTheme = () => {
  return useThemeStore.getState().resolvedTheme
}

/**
 * 检查是否为暗色主题
 */
export const isDarkTheme = () => {
  return useThemeStore.getState().resolvedTheme === 'dark'
}

/**
 * 主题相关的工具函数
 */
export const themeUtils = {
  /**
   * 根据主题返回不同的值
   */
  themeValue: <T>(lightValue: T, darkValue: T): T => {
    return isDarkTheme() ? darkValue : lightValue
  },
  
  /**
   * 获取主题相关的 CSS 变量
   */
  getCSSVariable: (variable: string): string => {
    return getComputedStyle(document.documentElement)
      .getPropertyValue(variable)
      .trim()
  },
  
  /**
   * 设置 CSS 变量
   */
  setCSSVariable: (variable: string, value: string): void => {
    document.documentElement.style.setProperty(variable, value)
  },
  
  /**
   * 获取主题相关的颜色
   */
  getThemeColor: (colorName: string): string => {
    return themeUtils.getCSSVariable(`--${colorName}`)
  },
}

/**
 * React Hook 用于监听主题变化
 */
export const useThemeEffect = (callback: (theme: 'light' | 'dark') => void) => {
  const resolvedTheme = useThemeStore((state) => state.resolvedTheme)
  
  React.useEffect(() => {
    callback(resolvedTheme)
  }, [resolvedTheme, callback])
}