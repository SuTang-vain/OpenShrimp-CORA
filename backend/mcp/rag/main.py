#!/usr/bin/env python3
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(title="MCP-RAG Service", version="0.1.0")


class ToolInfo(BaseModel):
    name: str
    description: str
    schema: Dict[str, Any]


class InvokeRequest(BaseModel):
    tool: str
    input: Dict[str, Any]


class InvokeResponse(BaseModel):
    tool: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


TOOLS: List[ToolInfo] = [
    ToolInfo(
        name="rag_query",
        description="Semantic search over indexed documents",
        schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "default": 5},
                "strategy": {"type": "string", "default": "similarity"},
                "language": {"type": "string", "default": "zh"}
            },
            "required": ["query"]
        }
    )
]


@app.get("/mcp/tools")
def list_tools() -> Dict[str, Any]:
    return {"tools": [t.model_dump() for t in TOOLS]}


@app.post("/mcp/invoke", response_model=InvokeResponse)
async def invoke_tool(req: InvokeRequest) -> InvokeResponse:
    if req.tool != "rag_query":
        raise HTTPException(status_code=404, detail=f"Unsupported tool: {req.tool}")

    cora_url = os.getenv("CORA_URL", "http://cora:8000")
    timeout_s = float(os.getenv("MCP_RAG_TIMEOUT", "30.0"))
    payload = {
        "query": req.input.get("query"),
        "top_k": req.input.get("top_k", 5),
        "strategy": req.input.get("strategy", "similarity"),
        "language": req.input.get("language", "zh")
    }

    if not payload["query"]:
        raise HTTPException(status_code=400, detail="Missing field: input.query")

    async with httpx.AsyncClient(timeout=timeout_s) as client:
        try:
            r = await client.post(f"{cora_url}/api/rag", json=payload)
            r.raise_for_status()
            data = r.json()
            return InvokeResponse(tool=req.tool, success=True, result=data)
        except httpx.HTTPStatusError as e:
            return InvokeResponse(tool=req.tool, success=False, error=f"Upstream {e.response.status_code}: {e.response.text}")
        except Exception as e:
            return InvokeResponse(tool=req.tool, success=False, error=str(e))


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "tools": len(TOOLS)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.mcp.rag.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8001")))