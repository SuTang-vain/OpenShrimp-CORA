from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from backend.core.auth import get_current_user
from backend.infrastructure.graph.neo4j_client import Neo4jClient

router = APIRouter(prefix="/mcp/graph", tags=["MCP-Graph"])

class GraphBuildInput(BaseModel):
    text: Optional[str] = Field(None, description="原始文本，用于抽取实体与关系")
    write_to: str = Field("memory", description="写入目标: memory 或 neo4j")

class GraphQueryInput(BaseModel):
    query: str = Field(..., description="图查询表达式或自然语言查询")
    top_k: int = Field(5, description="返回的最大节点/关系数量")

@router.post("/build")
async def mcp_graph_build(payload: GraphBuildInput, user: dict = Depends(get_current_user)):
    try:
        # 简化版图谱构建：仅在 Neo4j 可用时写入一个占位节点
        if payload.write_to == "neo4j":
            db = Neo4jClient.from_store()
            if not db:
                raise HTTPException(status_code=400, detail="Neo4j 未配置或连接失败")
            db.run_query("MERGE (n:Placeholder {name: $name})", {"name": (payload.text or "MCP-Graph")[:64]})
            return {"status": "ok", "write_to": "neo4j", "nodes": 1, "relations": 0}
        # 内存占位响应
        return {"status": "ok", "write_to": "memory", "nodes": 0, "relations": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"构建图谱失败: {e}")

@router.post("/query")
async def mcp_graph_query(payload: GraphQueryInput, user: dict = Depends(get_current_user)):
    try:
        # 简化版图查询：若 Neo4j 可用，执行一条安全查询；否则返回占位结果
        db = Neo4jClient.from_store()
        if db:
            res = db.run_query("MATCH (n) RETURN n.name AS name LIMIT $top_k", {"top_k": payload.top_k})
            return {"results": res, "source": "neo4j"}
        return {"results": [], "source": "memory"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图查询失败: {e}")
