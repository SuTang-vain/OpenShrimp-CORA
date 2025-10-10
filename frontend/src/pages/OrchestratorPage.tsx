import React from 'react'
import OrchestratorPanel from '@/components/orchestrator/OrchestratorPanel'

const OrchestratorPage: React.FC = () => {
  return (
    <div className="max-w-6xl mx-auto">
      <div className="py-4">
        <h1 className="text-2xl font-bold">Orchestrator 控制台</h1>
        <p className="text-sm text-muted-foreground mt-1">启动任务、查看事件流（SSE）与产出（最小闭环）。</p>
      </div>
      <OrchestratorPanel />
    </div>
  )
}

export default OrchestratorPage