#!/usr/bin/env python3
import os
from typing import Dict, Any, List, Optional

import yaml
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class ToolDef(BaseModel):
    name: str
    description: str
    url: str
    schema: Dict[str, Any]


class InvokeRequest(BaseModel):
    tool: str
    input: Dict[str, Any]


class InvokeResponse(BaseModel):
    tool: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


app = FastAPI(title="Strata MCP Server (PoC)", version="0.1.0")


def _load_config() -> Dict[str, Any]:
    cfg_path = os.getenv("STRATA_CONFIG", os.path.join(os.path.dirname(__file__), "config.yaml"))
    if not os.path.exists(cfg_path):
        return {"tools": []}
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"tools": []}


def _index_tools(cfg: Dict[str, Any]) -> Dict[str, ToolDef]:
    tools: List[Dict[str, Any]] = cfg.get("tools", [])
    index: Dict[str, ToolDef] = {}
    for t in tools:
        try:
            td = ToolDef(**t)
            index[td.name] = td
        except Exception:
            # 跳过非法配置项
            continue
    return index


_config: Dict[str, Any] = _load_config()
_tool_index: Dict[str, ToolDef] = _index_tools(_config)


@app.get("/tools")
def list_tools() -> Dict[str, Any]:
    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "schema": t.schema,
            }
            for t in _tool_index.values()
        ]
    }


@app.post("/invoke", response_model=InvokeResponse)
async def invoke_tool(req: InvokeRequest) -> InvokeResponse:
    tool = _tool_index.get(req.tool)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {req.tool}")

    timeout_s = float(os.getenv("STRATA_INVOKE_TIMEOUT", "30.0"))
    async with httpx.AsyncClient(timeout=timeout_s) as client:
        try:
            # 转发为 MCP 服务的统一协议
            # 期望目标服务实现 POST /mcp/invoke，接受 {tool, input}
            r = await client.post(tool.url, json={"tool": req.tool, "input": req.input})
            r.raise_for_status()
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text}
            return InvokeResponse(tool=req.tool, success=True, result=data)
        except httpx.HTTPStatusError as e:
            return InvokeResponse(tool=req.tool, success=False, error=f"Upstream error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            return InvokeResponse(tool=req.tool, success=False, error=str(e))


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "tools": len(_tool_index)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("strata.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8080")))