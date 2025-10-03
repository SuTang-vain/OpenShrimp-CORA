import * as React from 'react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  User,
  Mail,
  Lock,
  Phone,
  Eye,
  EyeOff,
  Github,
  Chrome,
  ArrowRight,
  CheckCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react'

import { useAuthStore } from '@/stores/authStore'
import type { RegisterRequest } from '@/types'
import { cn } from '@/utils/cn'

/**
 * 表单验证错误类型
 */
interface FormErrors {
  username?: string
  email?: string
  phone?: string
  password?: string
  confirmPassword?: string
  general?: string
}

/**
 * 表单数据类型
 */
interface FormData {
  username: string
  email: string
  phone: string
  password: string
  confirmPassword: string
}

/**
 * 用户注册页面组件
 * 提供用户注册功能，包含表单验证和第三方登录预留接口
 */
const RegisterPage: React.FC = () => {
  const navigate = useNavigate()
  const { register } = useAuthStore()

  // 表单状态
  const [formData, setFormData] = useState<FormData>({
    username: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
  })

  // UI状态
  const [errors, setErrors] = useState<FormErrors>({})
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)

  /**
   * 验证邮箱格式
   */
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  /**
   * 验证用户名格式
   */
  const validateUsername = (username: string): boolean => {
    const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/
    return usernameRegex.test(username)
  }

  /**
   * 验证手机号格式（支持国际格式）
   */
  const validatePhone = (phone: string): boolean => {
    if (!phone) return true // 手机号是可选的
    const phoneRegex = /^(\+\d{1,3}[- ]?)?\d{10,14}$/
    return phoneRegex.test(phone.replace(/\s/g, ''))
  }

  /**
   * 验证密码强度
   */
  const validatePassword = (password: string): boolean => {
    // 至少8位，包含字母和数字
    const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$/
    return passwordRegex.test(password)
  }

  /**
   * 表单验证
   */
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    // 验证用户名
    if (!formData.username) {
      newErrors.username = '用户名不能为空'
    } else if (!validateUsername(formData.username)) {
      newErrors.username = '用户名只能包含字母、数字、下划线，长度3-20字符'
    }

    // 验证邮箱
    if (!formData.email) {
      newErrors.email = '邮箱地址不能为空'
    } else if (!validateEmail(formData.email)) {
      newErrors.email = '请输入有效的邮箱地址'
    }

    // 验证手机号（可选）
    if (formData.phone && !validatePhone(formData.phone)) {
      newErrors.phone = '请输入有效的手机号码'
    }

    // 验证密码
    if (!formData.password) {
      newErrors.password = '密码不能为空'
    } else if (!validatePassword(formData.password)) {
      newErrors.password = '密码至少8位，需包含字母和数字'
    }

    // 验证确认密码
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = '请确认密码'
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = '两次输入的密码不一致'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  /**
   * 处理输入变化
   */
  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    
    // 清除对应字段的错误
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }))
    }
  }

  /**
   * 处理表单提交
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    setIsLoading(true)
    setErrors({})

    try {
      const registerData: RegisterRequest = {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        confirmPassword: formData.confirmPassword,
      }

      await register(registerData)
      
      setIsSuccess(true)
      
      // 延迟跳转，让用户看到成功提示
      setTimeout(() => {
        navigate('/', { replace: true })
      }, 2000)
      
    } catch (error: any) {
      console.error('注册失败:', error)
      setErrors({
        general: error.message || '注册失败，请稍后重试'
      })
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * 处理第三方登录（暂时禁用）
   */
  const handleThirdPartyLogin = (provider: 'github' | 'google') => {
    // TODO: 实现第三方登录逻辑
    console.log(`${provider} 登录即将推出`)
  }

  // 如果注册成功，显示成功页面
  if (isSuccess) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
          <div className="mb-6">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-gray-900 mb-2">注册成功！</h1>
            <p className="text-gray-600">
              欢迎加入 Shrimp Agent，正在为您跳转到首页...
            </p>
          </div>
          <div className="flex items-center justify-center">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            <span className="ml-2 text-sm text-gray-500">跳转中...</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl overflow-hidden">
        {/* 头部 */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-8 text-white text-center">
          <h1 className="text-2xl font-bold mb-2">创建账户</h1>
          <p className="text-blue-100">加入 Shrimp Agent，开启智能搜索之旅</p>
        </div>

        {/* 表单内容 */}
        <div className="p-8">
          {/* 第三方登录预留区域 */}
          <div className="mb-6">
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => handleThirdPartyLogin('github')}
                disabled
                className="flex items-center justify-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-500 bg-gray-50 cursor-not-allowed"
              >
                <Github className="h-4 w-4 mr-2" />
                GitHub
                <span className="ml-1 text-xs">(即将推出)</span>
              </button>
              <button
                type="button"
                onClick={() => handleThirdPartyLogin('google')}
                disabled
                className="flex items-center justify-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-500 bg-gray-50 cursor-not-allowed"
              >
                <Chrome className="h-4 w-4 mr-2" />
                Google
                <span className="ml-1 text-xs">(即将推出)</span>
              </button>
            </div>
            
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">或使用邮箱注册</span>
              </div>
            </div>
          </div>

          {/* 注册表单 */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* 通用错误提示 */}
            {errors.general && (
              <div className="flex items-center p-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg">
                <AlertCircle className="h-4 w-4 mr-2 flex-shrink-0" />
                {errors.general}
              </div>
            )}

            {/* 用户名 */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                用户名 <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  id="username"
                  type="text"
                  value={formData.username}
                  onChange={(e) => handleInputChange('username', e.target.value)}
                  className={cn(
                    'w-full pl-10 pr-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                    errors.username ? 'border-red-300 bg-red-50' : 'border-gray-300'
                  )}
                  placeholder="输入用户名（3-20字符）"
                  disabled={isLoading}
                />
              </div>
              {errors.username && (
                <p className="mt-1 text-sm text-red-600">{errors.username}</p>
              )}
            </div>

            {/* 邮箱 */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                邮箱地址 <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className={cn(
                    'w-full pl-10 pr-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                    errors.email ? 'border-red-300 bg-red-50' : 'border-gray-300'
                  )}
                  placeholder="输入邮箱地址"
                  disabled={isLoading}
                />
              </div>
              {errors.email && (
                <p className="mt-1 text-sm text-red-600">{errors.email}</p>
              )}
            </div>

            {/* 手机号（可选） */}
            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
                手机号码 <span className="text-gray-400">(可选)</span>
              </label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  id="phone"
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                  className={cn(
                    'w-full pl-10 pr-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                    errors.phone ? 'border-red-300 bg-red-50' : 'border-gray-300'
                  )}
                  placeholder="输入手机号码（支持国际格式）"
                  disabled={isLoading}
                />
              </div>
              {errors.phone && (
                <p className="mt-1 text-sm text-red-600">{errors.phone}</p>
              )}
            </div>

            {/* 密码 */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                密码 <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  className={cn(
                    'w-full pl-10 pr-10 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                    errors.password ? 'border-red-300 bg-red-50' : 'border-gray-300'
                  )}
                  placeholder="输入密码（至少8位，包含字母和数字）"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  disabled={isLoading}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">{errors.password}</p>
              )}
            </div>

            {/* 确认密码 */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
                确认密码 <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={formData.confirmPassword}
                  onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                  className={cn(
                    'w-full pl-10 pr-10 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                    errors.confirmPassword ? 'border-red-300 bg-red-50' : 'border-gray-300'
                  )}
                  placeholder="再次输入密码"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  disabled={isLoading}
                >
                  {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>
              )}
            </div>

            {/* 提交按钮 */}
            <button
              type="submit"
              disabled={isLoading}
              className={cn(
                'w-full flex items-center justify-center px-4 py-2 border border-transparent rounded-lg text-sm font-medium text-white',
                'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700',
                'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'transition-all duration-200'
              )}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  注册中...
                </>
              ) : (
                <>
                  创建账户
                  <ArrowRight className="h-4 w-4 ml-2" />
                </>
              )}
            </button>
          </form>

          {/* 登录链接 */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              已有账户？{' '}
              <Link
                to="/login"
                className="font-medium text-blue-600 hover:text-blue-500 transition-colors"
              >
                立即登录
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RegisterPage