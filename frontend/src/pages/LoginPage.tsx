import * as React from 'react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { User, Lock, Eye, EyeOff, ArrowRight, AlertCircle, Loader2 } from 'lucide-react'

import { useAuthStore, useAuthEffect } from '@/stores/authStore'
import type { LoginRequest } from '@/types'
import { cn } from '@/utils/cn'

interface FormData {
  username: string
  password: string
  rememberMe: boolean
}

interface FormErrors {
  username?: string
  password?: string
  submit?: string
}

const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const { login } = useAuthStore()

  const [formData, setFormData] = useState<FormData>({
    username: '',
    password: '',
    rememberMe: true,
  })
  const [errors, setErrors] = useState<FormErrors>({})
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  // 根据认证状态变化自动跳转到控制台
  useAuthEffect((isAuthenticated) => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true })
    }
  })

  const validate = (): boolean => {
    const newErrors: FormErrors = {}

    if (!formData.username.trim()) {
      newErrors.username = '请输入用户名'
    }

    if (!formData.password) {
      newErrors.password = '请输入密码'
    } else if (formData.password.length < 6) {
      newErrors.password = '密码长度至少6位'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { name, value, type, checked } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})

    if (!validate()) return

    setIsLoading(true)
    try {
      const payload: LoginRequest = {
        username: formData.username.trim(),
        password: formData.password,
        rememberMe: formData.rememberMe,
      }

      await login(payload)
      // 读取最新认证状态后再跳转，避免竞态
      if (useAuthStore.getState().isAuthenticated) {
        navigate('/dashboard', { replace: true })
      }
    } catch (error: any) {
      const message = error?.message || '登录失败，请检查用户名或密码'
      setErrors({ submit: message })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-lg mx-auto px-10 py-12 rounded-xl border bg-card shadow-sm">
        {/* 标题 */}
        <div className="text-center space-y-2 mb-8">
          <h1 className="text-3xl font-bold">欢迎登录</h1>
          <p className="text-muted-foreground text-base">使用您的账户登录以继续</p>
        </div>

        {/* 表单 */}
        <form className="space-y-7" onSubmit={handleSubmit} noValidate>
          {/* 用户名 */}
          <div>
            <label htmlFor="username" className="block text-base font-medium mb-2">用户名</label>
            <div className={cn('relative flex items-center')}> 
              <User className="h-7 w-7 text-muted-foreground absolute left-3" />
              <input
                id="username"
                name="username"
                type="text"
                placeholder="请输入用户名"
                value={formData.username}
                onChange={handleChange}
                className={cn(
                  'pl-12 input input-bordered input-lg text-lg w-full',
                  errors.username && 'input-error'
                )}
              />
            </div>
            {errors.username && (
              <p className="mt-2 text-sm text-destructive flex items-center">
                <AlertCircle className="h-4 w-4 mr-1" />{errors.username}
              </p>
            )}
          </div>

          {/* 密码 */}
          <div>
            <label htmlFor="password" className="block text-base font-medium mb-2">密码</label>
            <div className="relative flex items-center">
              <Lock className="h-7 w-7 text-muted-foreground absolute left-3" />
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="请输入密码"
                value={formData.password}
                onChange={handleChange}
                className={cn(
                  'pl-12 pr-12 input input-bordered input-lg text-lg w-full',
                  errors.password && 'input-error'
                )}
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3 text-muted-foreground hover:text-foreground"
                aria-label={showPassword ? '隐藏密码' : '显示密码'}
              >
                {showPassword ? <EyeOff className="h-6 w-6" /> : <Eye className="h-6 w-6" />}
              </button>
            </div>
            {errors.password && (
              <p className="mt-2 text-sm text-destructive flex items-center">
                <AlertCircle className="h-4 w-4 mr-1" />{errors.password}
              </p>
            )}
          </div>

          {/* 记住我 */}
          <div className="flex items-center justify-between">
            <label className="inline-flex items-center space-x-2">
              <input
                type="checkbox"
                name="rememberMe"
                checked={formData.rememberMe}
                onChange={handleChange}
                className="checkbox checkbox-lg"
              />
              <span className="text-base text-muted-foreground">记住我</span>
            </label>
            <Link to="/register" className="text-sm text-primary hover:text-primary/80">
              还没有账户？去注册
            </Link>
          </div>

          {/* 提交按钮 */}
          <button
            type="submit"
            className="btn btn-primary btn-lg w-full h-12 text-lg"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="h-6 w-6 mr-2 animate-spin" /> 登录中...
              </>
            ) : (
              <>
                登录 <ArrowRight className="h-6 w-6 ml-2" />
              </>
            )}
          </button>

          {/* 提交错误 */}
          {errors.submit && (
            <div className="mt-4 p-3 rounded-md bg-destructive/10 text-destructive text-sm flex items-center">
              <AlertCircle className="h-4 w-4 mr-2" />
              {errors.submit}
            </div>
          )}
        </form>
      </div>
    </div>
  )
}

export default LoginPage