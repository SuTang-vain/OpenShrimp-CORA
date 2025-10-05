from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict

from backend.core.auth import get_current_user
from backend.shared.secure_store import SecureStore
from backend.infrastructure.graph.neo4j_client import Neo4jClient

router = APIRouter(prefix="/mcp/services", tags=["MCP-Services"])

@router.get("/providers")
async def mcp_list_providers(user: dict = Depends(get_current_user)):
    return {
        "providers": [
            {"key": "openai", "desc": "OpenAI LLM"},
            {"key": "ollama", "desc": "Ollama Local LLM"},
            {"key": "neo4j", "desc": "Neo4j Graph DB"}
        ]
    }

class CredentialPayload(BaseModel):
    provider: str
    credentials: Dict[str, str]

@router.post("/credentials")
async def mcp_save_credentials(payload: CredentialPayload, user: dict = Depends(get_current_user)):
    try:
        store = SecureStore()
        store.save(f"credentials:{payload.provider}", payload.credentials)
        return {"status": "ok", "provider": payload.provider}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存凭据失败: {e}")

@router.post("/test")
async def mcp_test_service(payload: CredentialPayload, user: dict = Depends(get_current_user)):
    try:
        if payload.provider == "neo4j":
            db = Neo4jClient.from_store()
            if not db:
                return {"provider": "neo4j", "ok": False, "message": "未配置或连接失败"}
            res = db.run_query("RETURN 1 AS ok")
            return {"provider": "neo4j", "ok": True, "result": res}
        # 其它服务占位返回
        return {"provider": payload.provider, "ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务测试失败: {e}")
