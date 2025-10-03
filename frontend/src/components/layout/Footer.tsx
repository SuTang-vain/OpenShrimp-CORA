import * as React from 'react'
import { Link } from 'react-router-dom'
import { Heart, Github, Mail, ExternalLink } from 'lucide-react'

import { cn } from '@/utils/cn'
import logo from '@/assets/OpenShrimp.jpg'

/**
 * 底部组件属性
 */
interface FooterProps {
  className?: string
}

/**
 * 底部链接接口
 */
interface FooterLink {
  label: string
  href: string
  external?: boolean
}

/**
 * 底部链接组
 */
interface FooterLinkGroup {
  title: string
  links: FooterLink[]
}

/**
 * 底部链接配置
 */
const footerLinks: FooterLinkGroup[] = [
  {
    title: '产品',
    links: [
      { label: '功能特性', href: '/features' },
      { label: '定价方案', href: '/pricing' },
      { label: '更新日志', href: '/changelog' },
      { label: '路线图', href: '/roadmap' },
    ],
  },
  {
    title: '资源',
    links: [
      { label: '文档中心', href: '/docs', external: true },
      { label: 'API 文档', href: '/api-docs', external: true },
      { label: '帮助中心', href: '/help' },
      { label: '社区论坛', href: '/community', external: true },
    ],
  },
  {
    title: '公司',
    links: [
      { label: '关于我们', href: '/about' },
      { label: '联系我们', href: '/contact' },
      { label: '加入我们', href: '/careers' },
      { label: '媒体资源', href: '/press' },
    ],
  },
  {
    title: '法律',
    links: [
      { label: '隐私政策', href: '/privacy' },
      { label: '服务条款', href: '/terms' },
      { label: 'Cookie 政策', href: '/cookies' },
      { label: '许可协议', href: '/license' },
    ],
  },
]

/**
 * 社交媒体链接
 */
const socialLinks = [
  {
    label: 'GitHub',
    href: 'https://github.com/shrimp-team/shrimp-agent',
    icon: Github,
  },
  {
    label: '邮箱',
    href: 'mailto:contact@shrimp-agent.com',
    icon: Mail,
  },
]

/**
 * 底部组件
 * 提供网站的底部信息、链接和版权声明
 */
const Footer: React.FC<FooterProps> = ({ className }) => {
  const currentYear = new Date().getFullYear()

  return (
    <footer className={cn('bg-card border-t mt-auto', className)}>
      <div className="container-responsive">
        {/* 主要内容区域 */}
        <div className="py-12">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-8">
            {/* 品牌信息 */}
            <div className="lg:col-span-2">
              <div className="flex items-center space-x-2 mb-4">
                <img src={logo} alt="OpenShrimp" className="w-8 h-8 rounded-lg object-contain" />
                <span className="font-bold text-xl text-gradient">Shrimp Agent</span>
              </div>
              
              <p className="text-muted-foreground text-sm mb-6 max-w-sm">
                智能搜索与文档管理平台，让知识管理变得更加简单高效。
                基于先进的 AI 技术，为您提供精准的搜索体验。
              </p>
              
              {/* 社交媒体链接 */}
              <div className="flex items-center space-x-4">
                {socialLinks.map((social) => {
                  const Icon = social.icon
                  return (
                    <a
                      key={social.label}
                      href={social.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-muted-foreground hover:text-foreground transition-colors"
                      aria-label={social.label}
                    >
                      <Icon className="h-5 w-5" />
                    </a>
                  )
                })}
              </div>
            </div>

            {/* 链接组 */}
            {footerLinks.map((group) => (
              <div key={group.title} className="">
                <h3 className="font-semibold text-foreground mb-4">
                  {group.title}
                </h3>
                <ul className="space-y-3">
                  {group.links.map((link) => (
                    <li key={link.label}>
                      {link.external ? (
                        <a
                          href={link.href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center space-x-1"
                        >
                          <span>{link.label}</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      ) : (
                        <Link
                          to={link.href}
                          className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                        >
                          {link.label}
                        </Link>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* 分隔线 */}
        <div className="border-t" />

        {/* 底部版权信息 */}
        <div className="py-6">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            {/* 版权声明 */}
            <div className="flex items-center space-x-1 text-sm text-muted-foreground">
              <span>© {currentYear} Shrimp Team. 保留所有权利.</span>
            </div>

            {/* 技术信息 */}
            <div className="flex items-center space-x-4 text-sm text-muted-foreground">
              <span className="flex items-center space-x-1">
                <span>Made with</span>
                <Heart className="h-4 w-4 text-red-500" />
                <span>by Shrimp Team</span>
              </span>
              
              <span className="hidden md:block">|</span>
              
              <span>v2.0.0</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer