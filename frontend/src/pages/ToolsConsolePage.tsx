import React from 'react'
import ToolDiscoveryPanel from '@/components/mcp/ToolDiscoveryPanel'

const ToolsConsolePage: React.FC = () => {
  return (
    <div className="max-w-6xl mx-auto">
      <div className="py-4">
        <h1 className="text-2xl font-bold">工具控制台（Strata MCP）</h1>
        <p className="text-sm text-muted-foreground mt-1">
          通过 Strata 自动发现工具、按 Schema 配置参数并直接调用，结果可追踪。
        </p>
      </div>
      <ToolDiscoveryPanel />
    </div>
  )
}

export default ToolsConsolePage