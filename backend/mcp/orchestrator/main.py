import asyncio
import os
import time
import uuid
from typing import Any, Dict, Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx


app = FastAPI(title="MCP Orchestrator (PoC)", version="0.1.0")


class StartRequest(BaseModel):
  task: str
  input: Dict[str, Any] = {}


class StartResponse(BaseModel):
  id: str
  status: str


class StatusResponse(BaseModel):
  id: str
  status: str


class ArtifactResponse(BaseModel):
  id: str
  status: str
  artifact: Optional[Dict[str, Any]] = None


class TaskParam(BaseModel):
  name: str
  type: str  # string | number | boolean | select
  required: bool = False
  default: Optional[Any] = None
  options: Optional[List[Any]] = None


class TaskDef(BaseModel):
  type: str
  description: Optional[str] = None
  params: List[TaskParam] = []


class TasksResponse(BaseModel):
  tasks: List[TaskDef]


_tasks: Dict[str, Dict[str, Any]] = {}
_task_registry: Dict[str, TaskDef] = {
  "demo": TaskDef(
    type="demo",
    description="演示任务：回显输入并模拟三阶段闭环",
    params=[TaskParam(name="query", type="string", required=True, default="Hello MCP")],
  ),
  "graph_rag": TaskDef(
    type="graph_rag",
    description="图谱检索问答：输入问题并指定检索深度",
    params=[
      TaskParam(name="query", type="string", required=True, default="知识图谱如何用于检索增强生成？"),
      TaskParam(name="top_k", type="number", required=False, default=6),
      TaskParam(name="depth", type="number", required=False, default=1),
      TaskParam(name="mode", type="select", required=False, default="neighbors", options=["neighbors", "shortest"]),
      TaskParam(name="shortest_a", type="string", required=False, default=""),
      TaskParam(name="shortest_b", type="string", required=False, default=""),
      TaskParam(name="max_context_tokens", type="number", required=False, default=1200),
    ],
  ),
}


def _now_ms() -> int:
  return int(time.time() * 1000)


async def _run_task(task_id: str, name: str, payload: Dict[str, Any]):
  t = _tasks[task_id]
  t["status"] = "running"
  q: asyncio.Queue[str] = t["events"]

  async def emit(evt: Dict[str, Any]):
    await q.put(f"data: {evt}\n\n")

  if name == "graph_rag":
    # 真实后端 GraphRAG 接入
    await emit({"ts": _now_ms(), "stage": "prepare", "msg": "准备参数", "progress": 0.05})
    body = {
      "query": str(payload.get("query", "")),
      "top_k": int(payload.get("top_k", 6) or 6),
      "depth": int(payload.get("depth", 1) or 1),
      "mode": str(payload.get("mode", "neighbors") or "neighbors"),
      "shortest_a": (payload.get("shortest_a") or None) or None,
      "shortest_b": (payload.get("shortest_b") or None) or None,
      "max_context_tokens": int(payload.get("max_context_tokens", 1200) or 1200),
    }
    await emit({"ts": _now_ms(), "stage": "invoke", "msg": "调用后端 /api/v1/agents/graph-rag", "progress": 0.2})
    try:
      async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30) as client:
        resp = await client.post("/api/v1/agents/graph-rag", json=body)
        data = resp.json()
        if resp.status_code >= 400:
          raise HTTPException(status_code=resp.status_code, detail=str(data))
        await emit({"ts": _now_ms(), "stage": "retrieval", "msg": "检索与图谱上下文拼接", "progress": 0.6})
        # 后端统一响应：可能是 {success, data} 或直接数据
        result = data.get("data", data)
        t["artifact"] = {"task": name, "input": payload, "result": result}
        t["status"] = "completed"
        await emit({"ts": _now_ms(), "stage": "done", "msg": "GraphRAG 完成", "progress": 1.0})
    except Exception as e:
      t["artifact"] = {"task": name, "input": payload, "error": str(e)}
      t["status"] = "error"
      await emit({"ts": _now_ms(), "stage": "error", "msg": f"调用失败: {e}", "progress": 1.0})
  else:
    # 简单 CAMEL 闭环模拟：planner→executor→reviewer
    stages = ["planner", "executor", "reviewer"]
    for i, stage in enumerate(stages, start=1):
      await emit({"ts": _now_ms(), "stage": stage, "msg": f"stage {i} start", "progress": i / (len(stages) + 1)})
      await asyncio.sleep(0.5)
      await emit({"ts": _now_ms(), "stage": stage, "msg": "work in progress"})
      await asyncio.sleep(0.5)
      await emit({"ts": _now_ms(), "stage": stage, "msg": "stage complete"})

    t["artifact"] = {
      "task": name,
      "summary": "orchestrator demo artifact",
      "input": payload,
      "metrics": {"steps": len(stages), "duration_ms": 3 * 1000},
    }
    t["status"] = "completed"
    await emit({"ts": _now_ms(), "stage": "done", "msg": "task completed", "progress": 1.0})
  # 发送结束事件
  await q.put("event: end\n" + "data: {\"done\": true}\n\n")


@app.post("/orchestrator/tasks/start", response_model=StartResponse)
async def start(req: StartRequest) -> StartResponse:
  # 校验任务类型
  if req.task not in _task_registry:
    raise HTTPException(status_code=400, detail=f"unknown task: {req.task}")
  # 参数校验
  defn = _task_registry[req.task]
  errs: List[str] = []
  for p in defn.params:
    val = req.input.get(p.name)
    if p.required and (val is None or (isinstance(val, str) and val.strip() == "")):
      errs.append(f"参数 {p.name} 为必填")
      continue
    if val is not None:
      if p.type == "number" and not isinstance(val, (int, float)):
        errs.append(f"参数 {p.name} 需要数值")
      if p.type == "boolean" and not isinstance(val, bool):
        errs.append(f"参数 {p.name} 需要布尔值")
      if p.type == "select" and p.options and val not in p.options:
        errs.append(f"参数 {p.name} 不在可选范围")
  if errs:
    raise HTTPException(status_code=400, detail={"message": "参数校验失败", "errors": errs})
  tid = uuid.uuid4().hex
  _tasks[tid] = {"status": "pending", "events": asyncio.Queue(), "artifact": None}
  asyncio.create_task(_run_task(tid, req.task, req.input))
  return StartResponse(id=tid, status="pending")


@app.get("/orchestrator/tasks/{tid}/status", response_model=StatusResponse)
async def status(tid: str) -> StatusResponse:
  t = _tasks.get(tid)
  if not t:
    raise HTTPException(status_code=404, detail="task not found")
  return StatusResponse(id=tid, status=t["status"])


@app.get("/orchestrator/tasks/{tid}/artifact", response_model=ArtifactResponse)
async def artifact(tid: str) -> ArtifactResponse:
  t = _tasks.get(tid)
  if not t:
    raise HTTPException(status_code=404, detail="task not found")
  return ArtifactResponse(id=tid, status=t["status"], artifact=t["artifact"])


@app.get("/orchestrator/tasks", response_model=TasksResponse)
async def tasks() -> TasksResponse:
  return TasksResponse(tasks=list(_task_registry.values()))


@app.get("/orchestrator/tasks/{tid}/events")
async def events(tid: str):
  t = _tasks.get(tid)
  if not t:
    raise HTTPException(status_code=404, detail="task not found")
  q: asyncio.Queue[str] = t["events"]

  async def event_stream():
    # 先发送握手
    yield "retry: 1000\n\n"
    while True:
      msg = await q.get()
      yield msg
      if msg.startswith("event: end"):
        break

  return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
  import uvicorn
  uvicorn.run("backend.mcp.orchestrator.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8003")))