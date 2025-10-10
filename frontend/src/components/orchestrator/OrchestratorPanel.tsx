import React, { useEffect, useRef, useState } from 'react'
import { startTask, getTaskStatus, getTaskArtifact, getTasks } from '@/api/orchestrator'

type EventItem = { ts?: number; stage?: string; msg?: string; raw?: string }

type TaskParam = { name: string; type: 'string' | 'number' | 'boolean' | 'select'; required?: boolean; default?: any; options?: any[] }
type TaskDef = { type: string; description?: string; params: TaskParam[] }

export default function OrchestratorPanel() {
  const [tasks, setTasks] = useState<TaskDef[]>([])
  const [task, setTask] = useState('demo')
  const [paramValues, setParamValues] = useState<Record<string, any>>({ query: 'Hello MCP' })
  const [tid, setTid] = useState<string | null>(null)
  const [status, setStatus] = useState<string>('idle')
  const [events, setEvents] = useState<EventItem[]>([])
  const [artifact, setArtifact] = useState<any>(null)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [progress, setProgress] = useState<number>(0)
  const esRef = useRef<EventSource | null>(null)
  const pollingRef = useRef<any>(null)
  const reconnectTimer = useRef<any>(null)

  useEffect(() => {
    (async () => {
      try {
        const data = await getTasks()
        const list: TaskDef[] = data.tasks || []
        setTasks(list)
        const first = list.find(t => t.type === task) || list[0]
        if (first) {
          setTask(first.type)
          const initVals: Record<string, any> = {}
          for (const p of first.params || []) {
            if (p.default !== undefined) initVals[p.name] = p.default
            else initVals[p.name] = p.type === 'number' ? 0 : p.type === 'boolean' ? false : ''
          }
          setParamValues(initVals)
        }
      } catch {}
    })()
  }, [])

  useEffect(() => {
    const def = tasks.find(t => t.type === task)
    if (!def) return
    const next: Record<string, any> = { ...paramValues }
    for (const p of def.params || []) {
      if (!(p.name in next)) next[p.name] = p.default ?? (p.type === 'number' ? 0 : p.type === 'boolean' ? false : '')
    }
    setParamValues(next)
  }, [task])

  const validate = (): boolean => {
    const def = tasks.find(t => t.type === task)
    const errs: Record<string, string> = {}
    for (const p of def?.params || []) {
      const val = paramValues[p.name]
      if (p.required && (val === undefined || val === null || val === '')) {
        errs[p.name] = '必填'
        continue
      }
      if (val !== undefined && val !== null && val !== '') {
        if (p.type === 'number' && typeof val !== 'number') errs[p.name] = '需要数值'
        if (p.type === 'boolean' && typeof val !== 'boolean') errs[p.name] = '需要布尔值'
        if (p.type === 'select' && p.options && !p.options.includes(val)) errs[p.name] = '不在可选范围'
      }
    }
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const start = async () => {
    try {
      if (!validate()) return
      setStatus('starting')
      setEvents([])
      setArtifact(null)
      setProgress(0)
      const r = await startTask({ task, input: paramValues })
      const id = r.id
      setTid(id)
      setStatus(r.status || 'pending')
      // 连接 SSE
      const base = (import.meta as any).env.VITE_ORCH_BASE_URL || 'http://localhost:8003'
      const es = new EventSource(`${base}/orchestrator/tasks/${id}/events`)
      es.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data)
          setEvents((prev) => [...prev, data])
          if (typeof (data as any).progress === 'number') setProgress((data as any).progress)
        } catch {
          setEvents((prev) => [...prev, { raw: ev.data }])
        }
      }
      es.addEventListener('end', () => {
        es.close()
        esRef.current = null
      })
      es.onerror = () => {
        es.close()
        esRef.current = null
        // 断线重连（任务未完成时）
        if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
        reconnectTimer.current = setTimeout(() => {
          if (!id) return
          if (status === 'completed' || status === 'error') return
          const es2 = new EventSource(`${base}/orchestrator/tasks/${id}/events`)
          es2.onmessage = es.onmessage
          es2.addEventListener('end', () => { es2.close(); esRef.current = null })
          es2.onerror = () => { es2.close(); esRef.current = null }
          esRef.current = es2
        }, 1200)
      }
      esRef.current = es
      // 状态轮询
      if (pollingRef.current) clearInterval(pollingRef.current)
      pollingRef.current = setInterval(async () => {
        try {
          if (!id) return
          const s = await getTaskStatus(id)
          setStatus(s.status)
          if (s.status === 'completed') {
            clearInterval(pollingRef.current)
            const a = await getTaskArtifact(id)
            setArtifact(a.artifact)
            setProgress(1)
          }
        } catch {}
      }, 1000)
    } catch (e: any) {
      setStatus('error')
      setEvents((prev) => [...prev, { raw: e?.message || String(e) }])
    }
  }

  useEffect(() => {
    return () => {
      if (esRef.current) esRef.current.close()
      if (pollingRef.current) clearInterval(pollingRef.current)
    }
  }, [])

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Orchestrator 控制台</h2>
        <div className="text-xs text-muted-foreground">status: {status}</div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="space-y-2">
          <label className="text-sm">任务类型</label>
          <select className="border rounded px-2 py-2 w-full" value={task} onChange={(e) => setTask(e.target.value)}>
            {tasks.length === 0 ? <option value={task}>{task}</option> : tasks.map(t => (
              <option key={t.type} value={t.type}>{t.type}</option>
            ))}
          </select>
          {/* 参数表单 */}
          {(tasks.find(t => t.type === task)?.params || []).map((p) => (
            <div key={p.name} className="space-y-1">
              <label className="text-xs text-muted-foreground">{p.name}{p.required ? ' *' : ''}</label>
              {p.type === 'number' ? (
                <input type="number" className="border rounded px-2 py-2 w-full"
                  value={paramValues[p.name] ?? ''}
                  onChange={(e) => setParamValues(v => ({ ...v, [p.name]: Number(e.target.value) }))} />
              ) : p.type === 'boolean' ? (
                <label className="flex items-center space-x-2 text-xs">
                  <input type="checkbox" checked={!!paramValues[p.name]} onChange={(e) => setParamValues(v => ({ ...v, [p.name]: e.target.checked }))} />
                  <span>启用</span>
                </label>
              ) : p.type === 'select' ? (
                <select className="border rounded px-2 py-2 w-full" value={paramValues[p.name] ?? ''}
                  onChange={(e) => setParamValues(v => ({ ...v, [p.name]: e.target.value }))}>
                  {(p.options || []).map((opt, i) => <option key={i} value={opt}>{String(opt)}</option>)}
                </select>
              ) : (
                <input className="border rounded px-2 py-2 w-full" value={paramValues[p.name] ?? ''}
                  onChange={(e) => setParamValues(v => ({ ...v, [p.name]: e.target.value }))} />
              )}
              {errors[p.name] && <div className="text-[11px] text-red-600">{errors[p.name]}</div>}
            </div>
          ))}
          {/* 预览输入 */}
          <div className="text-xs text-muted-foreground">输入预览</div>
          <pre className="text-xs border rounded p-2 bg-muted h-24 overflow-auto">{JSON.stringify(paramValues, null, 2)}</pre>
          <button className="px-3 py-2 rounded bg-primary text-primary-foreground border" onClick={start}>
            启动任务
          </button>
        </div>
        <div>
          <div className="text-sm font-medium mb-2">事件流 {tid ? `(${tid})` : ''}</div>
          <div className="mb-2 h-2 bg-muted rounded">
            <div className="h-2 bg-blue-500 rounded" style={{ width: `${Math.round(progress * 100)}%`, transition: 'width 200ms ease' }} />
          </div>
          <div className="border rounded p-2 h-48 overflow-auto text-xs bg-muted">
            {events.length === 0 ? <div className="text-muted-foreground">暂无事件</div> : (
              <ul className="space-y-1">
                {events.map((e, idx) => (
                  <li key={idx}>
                    {e.ts ? <span className="text-muted-foreground mr-2">{e.ts}</span> : null}
                    {e.stage ? <span className="mr-2">[{e.stage}]</span> : null}
                    <span>{e.msg ?? e.raw}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      {artifact && (
        <div>
          <div className="text-sm font-medium mb-2">产出</div>
          <pre className="text-xs border rounded p-3 bg-muted overflow-auto max-h-64">{JSON.stringify(artifact, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}