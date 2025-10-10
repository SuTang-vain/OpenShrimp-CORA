import asyncio
import os
import time
import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel


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


_tasks: Dict[str, Dict[str, Any]] = {}


def _now_ms() -> int:
  return int(time.time() * 1000)


async def _run_task(task_id: str, name: str, payload: Dict[str, Any]):
  t = _tasks[task_id]
  t["status"] = "running"
  q: asyncio.Queue[str] = t["events"]

  async def emit(evt: Dict[str, Any]):
    await q.put(f"data: {evt}\n\n")

  # 简单 CAMEL 闭环模拟：planner→executor→reviewer
  stages = ["planner", "executor", "reviewer"]
  for i, stage in enumerate(stages, start=1):
    await emit({"ts": _now_ms(), "stage": stage, "msg": f"stage {i} start"})
    await asyncio.sleep(0.5)
    await emit({"ts": _now_ms(), "stage": stage, "msg": "work in progress"})
    await asyncio.sleep(0.5)
    await emit({"ts": _now_ms(), "stage": stage, "msg": "stage complete"})

  # 产出 artifact
  t["artifact"] = {
    "task": name,
    "summary": "orchestrator demo artifact",
    "input": payload,
    "metrics": {"steps": len(stages), "duration_ms": 3 * 1000},
  }
  t["status"] = "completed"
  await emit({"ts": _now_ms(), "stage": "done", "msg": "task completed"})
  # 发送结束事件
  await q.put("event: end\n" + "data: {\"done\": true}\n\n")


@app.post("/orchestrator/tasks/start", response_model=StartResponse)
async def start(req: StartRequest) -> StartResponse:
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