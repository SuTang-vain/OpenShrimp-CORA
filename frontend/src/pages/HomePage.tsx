import * as React from 'react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
// import { motion } from 'framer-motion'
import {
  Search,
  FileText,
  Zap,
  Shield,
  BarChart3,
  ArrowRight,
  Play,

  Star,
  Users,
  Clock,
  TrendingUp,
} from 'lucide-react'

import { useAuth } from '@/stores/authStore'
import { cn } from '@/utils/cn'

/**
 * 功能特性接口
 */
interface Feature {
  icon: React.ComponentType<{ className?: string }>
  title: string
  description: string
  color: string
}

/**
 * 统计数据接口
 */
interface Stat {
  icon: React.ComponentType<{ className?: string }>
  value: string
  label: string
  trend?: string
}

/**
 * 功能特性数据
 */
const features: Feature[] = [
  {
    icon: Search,
    title: '智能搜索',
    description: '基于 AI 的语义搜索，理解您的意图，提供精准的搜索结果',
    color: 'text-blue-500',
  },
  {
    icon: FileText,
    title: '文档管理',
    description: '支持多种文档格式，自动分析和索引，让文档管理变得简单',
    color: 'text-green-500',
  },
  {
    icon: Zap,
    title: '快速响应',
    description: '毫秒级搜索响应，实时结果展示，提升工作效率',
    color: 'text-yellow-500',
  },
  {
    icon: Shield,
    title: '安全可靠',
    description: '企业级安全保障，数据加密存储，保护您的隐私',
    color: 'text-red-500',
  },
  {
    icon: BarChart3,
    title: '数据分析',
    description: '深入的使用分析，帮助您了解搜索模式和优化策略',
    color: 'text-purple-500',
  },
  {
    icon: Users,
    title: '团队协作',
    description: '支持团队共享和协作，让知识在团队中流动',
    color: 'text-indigo-500',
  },
]

/**
 * 统计数据
 */
const stats: Stat[] = [
  {
    icon: Users,
    value: '10,000+',
    label: '活跃用户',
    trend: '+12%',
  },
  {
    icon: FileText,
    value: '1M+',
    label: '文档处理',
    trend: '+25%',
  },
  {
    icon: Search,
    value: '50M+',
    label: '搜索查询',
    trend: '+18%',
  },
  {
    icon: Clock,
    value: '99.9%',
    label: '服务可用性',
    trend: '+0.1%',
  },
]

/**
 * 首页组件
 * 展示产品介绍、功能特性和快速入门
 */
const HomePage: React.FC = () => {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')

  /**
   * 处理搜索提交
   */
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`)
    }
  }



  return (
    <div className="min-h-screen">
      {/* 英雄区域 */}
      <section className="relative py-20 lg:py-32 overflow-hidden">
        {/* 背景装饰 */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-secondary/5" />
        <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-secondary/10 rounded-full blur-3xl" />

        <div className="relative container-responsive">
          <div className="text-center max-w-4xl mx-auto">
            <div className="mb-6">
              <span className="inline-flex items-center px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium">
                <Star className="h-4 w-4 mr-2" />
                全新 v2.0 版本发布
              </span>
            </div>

            <h1 className="text-4xl lg:text-6xl font-bold text-foreground mb-6">
              智能搜索，
              <span className="text-gradient">重新定义</span>
              <br />
              知识管理体验
            </h1>

            <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              基于先进的 AI 技术，KrillNet 为您提供智能化的文档搜索和管理解决方案，
              让知识触手可及，让工作更加高效。
            </p>

            {/* 搜索框 */}
            <div className="mb-8">
              <form onSubmit={handleSearch} className="max-w-2xl mx-auto">
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="搜索任何内容..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-12 pr-32 py-4 text-lg border border-border rounded-xl bg-background/50 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                  <button
                    type="submit"
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 btn btn-primary btn-md"
                  >
                    开始搜索
                  </button>
                </div>
              </form>
            </div>

            {/* 行动按钮 */}
            <div className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-4">
              {isAuthenticated ? (
                <Link to="/search" className="btn btn-primary btn-lg">
                  开始使用
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              ) : (
                <Link to="/register" className="btn btn-primary btn-lg">
                  免费注册
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              )}
              
              <button className="btn btn-outline btn-lg">
                <Play className="mr-2 h-5 w-5" />
                观看演示
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 统计数据 */}
      <section className="py-16 bg-muted/30">
        <div className="container-responsive">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            {stats.map((stat, index) => {
              const Icon = stat.icon
              return (
                <div
                  key={index}
                  className="text-center"
                >
                  <div className="inline-flex items-center justify-center w-12 h-12 bg-primary/10 rounded-lg mb-4">
                    <Icon className="h-6 w-6 text-primary" />
                  </div>
                  <div className="text-3xl font-bold text-foreground mb-1">
                    {stat.value}
                  </div>
                  <div className="text-sm text-muted-foreground mb-1">
                    {stat.label}
                  </div>
                  {stat.trend && (
                    <div className="flex items-center justify-center text-xs text-green-600">
                      <TrendingUp className="h-3 w-3 mr-1" />
                      {stat.trend}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* 功能特性 */}
      <section className="py-20">
        <div className="container-responsive">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold text-foreground mb-4">
              强大的功能特性
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              我们提供全面的解决方案，满足您的各种需求
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon
              return (
                <div
                  key={index}
                  className="card p-6 hover:shadow-lg transition-shadow"
                >
                  <div className="flex items-center mb-4">
                    <div className={cn('p-2 rounded-lg bg-muted', feature.color)}>
                      <Icon className="h-6 w-6" />
                    </div>
                    <h3 className="text-xl font-semibold text-foreground ml-3">
                      {feature.title}
                    </h3>
                  </div>
                  <p className="text-muted-foreground">
                    {feature.description}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* 快速开始 */}
      <section className="py-20 bg-muted/30">
        <div className="container-responsive">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl lg:text-4xl font-bold text-foreground mb-4">
                三步开始使用
              </h2>
              <p className="text-xl text-muted-foreground">
                简单几步，即可体验智能搜索的强大功能
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                {
                  step: '01',
                  title: '注册账户',
                  description: '创建您的免费账户，开始使用 KrillNet',
                },
                {
                  step: '02',
                  title: '上传文档',
                  description: '上传您的文档，系统会自动进行分析和索引',
                },
                {
                  step: '03',
                  title: '开始搜索',
                  description: '使用自然语言搜索，获得精准的结果',
                },
              ].map((item, index) => (
                <div
                  key={index}
                  className="text-center"
                >
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-primary text-primary-foreground rounded-full text-xl font-bold mb-4">
                    {item.step}
                  </div>
                  <h3 className="text-xl font-semibold text-foreground mb-2">
                    {item.title}
                  </h3>
                  <p className="text-muted-foreground">
                    {item.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 行动召唤 */}
      <section className="py-20">
        <div className="container-responsive">
          <div className="text-center max-w-3xl mx-auto">
            <h2 className="text-3xl lg:text-4xl font-bold text-foreground mb-4">
              准备好开始了吗？
            </h2>
            <p className="text-xl text-muted-foreground mb-8">
              加入数万用户的行列，体验智能搜索带来的效率提升
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-4">
              {isAuthenticated ? (
                <Link to="/documents" className="btn btn-primary btn-lg">
                  上传第一个文档
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              ) : (
                <>
                  <Link to="/register" className="btn btn-primary btn-lg">
                    免费开始使用
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Link>
                  <Link to="/login" className="btn btn-outline btn-lg">
                    已有账户？登录
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default HomePage