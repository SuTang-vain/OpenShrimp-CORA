import * as React from 'react'
import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  User,
  Bell,
  Shield,
  Palette,
  Database,
  Key,
  Download,
  Trash2,
  Save,
  Eye,
  EyeOff,
  Check,
  Search,
  Globe,
  Settings,

  RotateCcw,
} from 'lucide-react'
import { toast } from 'sonner'

import { useAuth } from '@/stores/authStore'
import { useThemeStore } from '@/stores/themeStore'
import { useSettings } from '@/stores/settingsStore'
import { cn } from '@/utils/cn'
import type { Theme } from '@/types'

/**
 * 设置页面组件
 * 提供用户个人设置、系统配置等功能
 */
const SettingsPage: React.FC = () => {
  const { user, updateUser } = useAuth()
  const { theme, setTheme } = useThemeStore()
  const {
    searchSources,
    searchBehavior,
    advanced,
    toggleSearchSource,
    updateSearchBehavior,
    updateAdvanced,
    resetSettings,
  } = useSettings()
  
  // 表单状态
  const [activeTab, setActiveTab] = useState('profile')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  
  // 个人信息表单
  const [profileForm, setProfileForm] = useState({
    username: user?.username || '',
    email: user?.email || '',
    avatar: user?.avatar || '',
  })
  
  // 密码修改表单
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  })
  
  // 通知设置
  const [notifications, setNotifications] = useState({
    emailNotifications: true,
    pushNotifications: true,
    searchAlerts: false,
    documentUpdates: true,
    systemUpdates: false,
  })
  
  // 隐私设置
  const [privacy, setPrivacy] = useState({
    profileVisibility: 'private',
    searchHistory: true,
    dataCollection: false,
    thirdPartySharing: false,
  })

  /**
   * 设置选项卡
   */
  const tabs = [
    {
      id: 'profile',
      label: '个人资料',
      icon: User,
    },
    {
      id: 'search',
      label: '搜索设置',
      icon: Search,
    },
    {
      id: 'notifications',
      label: '通知设置',
      icon: Bell,
    },
    {
      id: 'privacy',
      label: '隐私安全',
      icon: Shield,
    },
    {
      id: 'appearance',
      label: '外观设置',
      icon: Palette,
    },
    {
      id: 'advanced',
      label: '高级设置',
      icon: Settings,
    },
    {
      id: 'data',
      label: '数据管理',
      icon: Database,
    },
  ]

  /**
   * 保存个人资料
   */
  const saveProfile = async () => {
    setLoading(true)
    try {
      await updateUser(profileForm)
      toast.success('个人资料已更新')
    } catch (error) {
      toast.error('更新失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  /**
   * 修改密码
   */
  const changePassword = async () => {
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      toast.error('新密码与确认密码不匹配')
      return
    }
    
    if (passwordForm.newPassword.length < 8) {
      toast.error('密码长度至少为8位')
      return
    }
    
    setLoading(true)
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setPasswordForm({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      })
      
      toast.success('密码已更新')
    } catch (error) {
      toast.error('密码修改失败')
    } finally {
      setLoading(false)
    }
  }

  /**
   * 导出数据
   */
  const exportData = async () => {
    setLoading(true)
    try {
      // 模拟数据导出
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      const data = {
        user: user,
        settings: {
          notifications,
          privacy,
          theme,
        },
        exportDate: new Date().toISOString(),
      }
      
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json',
      })
      
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `shrimp-agent-data-${Date.now()}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      
      toast.success('数据导出成功')
    } catch (error) {
      toast.error('数据导出失败')
    } finally {
      setLoading(false)
    }
  }

  /**
   * 删除账户
   */
  const deleteAccount = async () => {
    const confirmed = window.confirm(
      '确定要删除账户吗？此操作不可撤销，所有数据将被永久删除。'
    )
    
    if (!confirmed) return
    
    setLoading(true)
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))
      toast.success('账户已删除')
      // 这里应该跳转到登录页面
    } catch (error) {
      toast.error('删除失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  /**
   * 渲染个人资料设置
   */
  const renderProfileSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">个人信息</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">用户名</label>
            <input
              type="text"
              value={profileForm.username}
              onChange={(e) => setProfileForm({ ...profileForm, username: e.target.value })}
              className="input w-full"
              placeholder="请输入用户名"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">邮箱地址</label>
            <input
              type="email"
              value={profileForm.email}
              onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
              className="input w-full"
              placeholder="请输入邮箱地址"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">头像URL</label>
            <input
              type="url"
              value={profileForm.avatar}
              onChange={(e) => setProfileForm({ ...profileForm, avatar: e.target.value })}
              className="input w-full"
              placeholder="请输入头像URL"
            />
          </div>
        </div>
      </div>
      
      <div>
        <h3 className="text-lg font-semibold mb-4">修改密码</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">当前密码</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={passwordForm.currentPassword}
                onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                className="input w-full pr-10"
                placeholder="请输入当前密码"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">新密码</label>
            <input
              type="password"
              value={passwordForm.newPassword}
              onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
              className="input w-full"
              placeholder="请输入新密码（至少8位）"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">确认新密码</label>
            <input
              type="password"
              value={passwordForm.confirmPassword}
              onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
              className="input w-full"
              placeholder="请再次输入新密码"
            />
          </div>
          
          <button
            onClick={changePassword}
            disabled={loading || !passwordForm.currentPassword || !passwordForm.newPassword}
            className="btn btn-outline btn-md"
          >
            <Key className="h-4 w-4 mr-2" />
            修改密码
          </button>
        </div>
      </div>
      
      <div className="flex justify-end">
        <button
          onClick={saveProfile}
          disabled={loading}
          className="btn btn-primary btn-md"
        >
          <Save className="h-4 w-4 mr-2" />
          保存更改
        </button>
      </div>
    </div>
  )

  /**
   * 渲染搜索设置
   */
  const renderSearchSettings = () => (
    <div className="space-y-6">
      {/* 搜索源配置 */}
      <div>
        <h3 className="text-lg font-semibold mb-4">搜索源配置</h3>
        <p className="text-sm text-muted-foreground mb-4">
          选择要使用的搜索引擎，可以同时启用多个搜索源。
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries({
            google: { name: 'Google', description: '全球最大的搜索引擎', icon: Globe },
            bing: { name: 'Bing', description: 'Microsoft 搜索引擎', icon: Globe },
            baidu: { name: '百度', description: '中文搜索引擎', icon: Globe },
            duckduckgo: { name: 'DuckDuckGo', description: '注重隐私的搜索引擎', icon: Shield },
          }).map(([key, source]) => {
            const Icon = source.icon
            const isEnabled = searchSources.find(source => source.id === key)?.enabled
            
            return (
              <div
                key={key}
                className={cn(
                  'card p-4 cursor-pointer transition-colors',
                  isEnabled ? 'ring-2 ring-primary bg-primary/5' : 'hover:bg-muted/50'
                )}
                onClick={() => {
                  toggleSearchSource(key)
                }}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    <Icon className="h-5 w-5 text-primary" />
                    <h4 className="font-medium">{source.name}</h4>
                  </div>
                  {isEnabled && <Check className="h-4 w-4 text-primary" />}
                </div>
                <p className="text-sm text-muted-foreground">{source.description}</p>
              </div>
            )
          })}
        </div>
      </div>
      
      {/* 搜索行为设置 */}
      <div>
        <h3 className="text-lg font-semibold mb-4">搜索行为</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              最大结果数量
              <span className="text-muted-foreground ml-1">({searchBehavior.maxResults})</span>
            </label>
            <input
              type="range"
              min="10"
              max="100"
              step="10"
              value={searchBehavior.maxResults}
              onChange={(e) => updateSearchBehavior({ maxResults: parseInt(e.target.value) })}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>10</span>
              <span>100</span>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">
              搜索超时时间
              <span className="text-muted-foreground ml-1">({searchBehavior.timeout}秒)</span>
            </label>
            <input
              type="range"
              min="5"
              max="60"
              step="5"
              value={searchBehavior.timeout}
              onChange={(e) => updateSearchBehavior({ timeout: parseInt(e.target.value) })}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>5秒</span>
              <span>60秒</span>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium">自动搜索建议</label>
              <p className="text-xs text-muted-foreground">输入时自动显示搜索建议</p>
            </div>
            <button
              onClick={() => updateSearchBehavior({ enableSuggestions: !searchBehavior.enableSuggestions })}
              className={cn(
                'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                searchBehavior.enableSuggestions ? 'bg-primary' : 'bg-muted'
              )}
            >
              <span
                className={cn(
                  'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                  searchBehavior.enableSuggestions ? 'translate-x-6' : 'translate-x-1'
                )}
              />
            </button>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium">保存搜索历史</label>
              <p className="text-xs text-muted-foreground">自动保存搜索记录</p>
            </div>
            <button
              onClick={() => updateSearchBehavior({ saveHistory: !searchBehavior.saveHistory })}
              className={cn(
                'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                searchBehavior.saveHistory ? 'bg-primary' : 'bg-muted'
              )}
            >
              <span
                className={cn(
                  'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                  searchBehavior.saveHistory ? 'translate-x-6' : 'translate-x-1'
                )}
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  )

  /**
   * 渲染通知设置
   */
  const renderNotificationSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">通知偏好</h3>
        
        <div className="space-y-4">
          {Object.entries({
            emailNotifications: '邮件通知',
            pushNotifications: '推送通知',
            searchAlerts: '搜索提醒',
            documentUpdates: '文档更新',
            systemUpdates: '系统更新',
          }).map(([key, label]) => (
            <div key={key} className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium">{label}</label>
                <p className="text-xs text-muted-foreground">
                  {key === 'emailNotifications' && '接收重要通知的邮件提醒'}
                  {key === 'pushNotifications' && '接收浏览器推送通知'}
                  {key === 'searchAlerts' && '搜索结果更新时通知'}
                  {key === 'documentUpdates' && '文档处理完成时通知'}
                  {key === 'systemUpdates' && '系统维护和更新通知'}
                </p>
              </div>
              
              <button
                onClick={() => setNotifications({
                  ...notifications,
                  [key]: !notifications[key as keyof typeof notifications]
                })}
                className={cn(
                  'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                  notifications[key as keyof typeof notifications]
                    ? 'bg-primary'
                    : 'bg-muted'
                )}
              >
                <span
                  className={cn(
                    'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                    notifications[key as keyof typeof notifications]
                      ? 'translate-x-6'
                      : 'translate-x-1'
                  )}
                />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  /**
   * 渲染隐私设置
   */
  const renderPrivacySettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">隐私控制</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">个人资料可见性</label>
            <select
              value={privacy.profileVisibility}
              onChange={(e) => setPrivacy({ ...privacy, profileVisibility: e.target.value })}
              className="input w-full"
            >
              <option value="public">公开</option>
              <option value="private">私有</option>
              <option value="friends">仅好友</option>
            </select>
          </div>
          
          {Object.entries({
            searchHistory: '保存搜索历史',
            dataCollection: '允许数据收集',
            thirdPartySharing: '第三方数据共享',
          }).map(([key, label]) => (
            <div key={key} className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium">{label}</label>
                <p className="text-xs text-muted-foreground">
                  {key === 'searchHistory' && '保存您的搜索记录以改善体验'}
                  {key === 'dataCollection' && '允许收集匿名使用数据'}
                  {key === 'thirdPartySharing' && '与合作伙伴共享匿名数据'}
                </p>
              </div>
              
              <button
                onClick={() => setPrivacy({
                  ...privacy,
                  [key]: !privacy[key as keyof typeof privacy]
                })}
                className={cn(
                  'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                  privacy[key as keyof typeof privacy]
                    ? 'bg-primary'
                    : 'bg-muted'
                )}
              >
                <span
                  className={cn(
                    'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                    privacy[key as keyof typeof privacy]
                      ? 'translate-x-6'
                      : 'translate-x-1'
                  )}
                />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  /**
   * 渲染外观设置
   */
  const renderAppearanceSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">主题设置</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { value: 'light', label: '浅色模式', description: '明亮清爽的界面' },
            { value: 'dark', label: '深色模式', description: '护眼的深色界面' },
            { value: 'system', label: '跟随系统', description: '自动切换主题' },
          ].map((option) => (
            <button
              key={option.value}
              onClick={() => setTheme(option.value as Theme)}
              className={cn(
                'card p-4 text-left transition-colors',
                theme === option.value
                  ? 'ring-2 ring-primary bg-primary/5'
                  : 'hover:bg-muted/50'
              )}
            >
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium">{option.label}</h4>
                {theme === option.value && (
                  <Check className="h-4 w-4 text-primary" />
                )}
              </div>
              <p className="text-sm text-muted-foreground">
                {option.description}
              </p>
            </button>
          ))}
        </div>
      </div>
    </div>
  )

  /**
   * 渲染高级设置
   */
  const renderAdvancedSettings = () => (
    <div className="space-y-6">
      {/* 性能设置 */}
      <div>
        <h3 className="text-lg font-semibold mb-4">性能优化</h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium">启用缓存</label>
              <p className="text-xs text-muted-foreground">缓存搜索结果以提高性能</p>
            </div>
            <button
              onClick={() => updateAdvanced({ cacheEnabled: !advanced.cacheEnabled })}
              className={cn(
                'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                advanced.cacheEnabled ? 'bg-primary' : 'bg-muted'
              )}
            >
              <span
                className={cn(
                  'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                  advanced.cacheEnabled ? 'translate-x-6' : 'translate-x-1'
                )}
              />
            </button>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">
              缓存过期时间
              <span className="text-muted-foreground ml-1">({advanced.cacheSize}MB)</span>
            </label>
            <input
              type="range"
              min="5"
              max="120"
              step="5"
              value={advanced.cacheSize}
              onChange={(e) => updateAdvanced({ cacheSize: parseInt(e.target.value) })}
              className="w-full"
              disabled={!advanced.cacheEnabled}
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>5分钟</span>
              <span>2小时</span>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">
              并发请求数
              <span className="text-muted-foreground ml-1">({advanced.retryAttempts})</span>
            </label>
            <input
              type="range"
              min="1"
              max="10"
              step="1"
              value={advanced.retryAttempts}
              onChange={(e) => updateAdvanced({ retryAttempts: parseInt(e.target.value) })}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>1</span>
              <span>10</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* 调试设置 */}
      <div>
        <h3 className="text-lg font-semibold mb-4">调试选项</h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium">调试模式</label>
              <p className="text-xs text-muted-foreground">显示详细的调试信息</p>
            </div>
            <button
              onClick={() => updateAdvanced({ debugMode: !advanced.debugMode })}
              className={cn(
                'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                advanced.debugMode ? 'bg-primary' : 'bg-muted'
              )}
            >
              <span
                className={cn(
                  'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                  advanced.debugMode ? 'translate-x-6' : 'translate-x-1'
                )}
              />
            </button>
          </div>
          

        </div>
      </div>
      
      {/* 实验性功能 */}
      <div>
        <h3 className="text-lg font-semibold mb-4">实验性功能</h3>
        <p className="text-sm text-muted-foreground mb-4">
          这些功能仍在开发中，可能不稳定。
        </p>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium">实验性功能</label>
              <p className="text-xs text-muted-foreground">启用实验性功能和特性</p>
            </div>
            <button
              onClick={() => updateAdvanced({ enableExperimentalFeatures: !advanced.enableExperimentalFeatures })}
              className={cn(
                'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                advanced.enableExperimentalFeatures ? 'bg-primary' : 'bg-muted'
              )}
            >
              <span
                className={cn(
                  'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                  advanced.enableExperimentalFeatures ? 'translate-x-6' : 'translate-x-1'
                )}
              />
            </button>
          </div>
        </div>
      </div>
      
      {/* 重置设置 */}
      <div className="border-t pt-6">
        <h3 className="text-lg font-semibold mb-4">重置设置</h3>
        <p className="text-sm text-muted-foreground mb-4">
          将所有设置恢复为默认值。
        </p>
        
        <button
          onClick={() => {
            if (window.confirm('确定要重置所有设置吗？此操作不可撤销。')) {
              resetSettings()
              toast.success('设置已重置为默认值')
            }
          }}
          className="btn btn-outline btn-md"
        >
          <RotateCcw className="h-4 w-4 mr-2" />
          重置所有设置
        </button>
      </div>
    </div>
  )

  /**
   * 渲染数据管理
   */
  const renderDataManagement = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">数据导出</h3>
        <p className="text-sm text-muted-foreground mb-4">
          导出您的所有数据，包括个人信息、设置和文档。
        </p>
        
        <button
          onClick={exportData}
          disabled={loading}
          className="btn btn-outline btn-md"
        >
          <Download className="h-4 w-4 mr-2" />
          导出数据
        </button>
      </div>
      
      <div className="border-t pt-6">
        <h3 className="text-lg font-semibold mb-4 text-destructive">危险操作</h3>
        <p className="text-sm text-muted-foreground mb-4">
          删除账户将永久删除您的所有数据，此操作不可撤销。
        </p>
        
        <button
          onClick={deleteAccount}
          disabled={loading}
          className="btn btn-destructive btn-md"
        >
          <Trash2 className="h-4 w-4 mr-2" />
          删除账户
        </button>
      </div>
    </div>
  )

  return (
    <div className="max-w-6xl mx-auto">
      {/* 页面头部 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">设置</h1>
        <p className="text-muted-foreground">
          管理您的账户设置和偏好
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* 侧边栏导航 */}
        <div className="lg:col-span-1">
          <nav className="space-y-2">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    'w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-left transition-colors',
                    activeTab === tab.id
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted text-muted-foreground'
                  )}
                >
                  <Icon className="h-5 w-5" />
                  <span className="font-medium">{tab.label}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* 主要内容区域 */}
        <div className="lg:col-span-3">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
            className="card p-6"
          >
            {activeTab === 'profile' && renderProfileSettings()}
            {activeTab === 'search' && renderSearchSettings()}
            {activeTab === 'notifications' && renderNotificationSettings()}
            {activeTab === 'privacy' && renderPrivacySettings()}
            {activeTab === 'appearance' && renderAppearanceSettings()}
            {activeTab === 'advanced' && renderAdvancedSettings()}
            {activeTab === 'data' && renderDataManagement()}
          </motion.div>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage
