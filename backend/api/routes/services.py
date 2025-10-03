import os
import socket
from typing import Dict, Any, List

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from backend.shared.secure_store import load_credentials, save_credentials
from backend.infrastructure.graph.neo4j_client import Neo4jClient


router = APIRouter()


class CredentialsInput(BaseModel):
    provider_id: str
    credentials: Dict[str, Any]


@router.get("/services/providers")
async def list_providers(request: Request):
    settings = None
    try:
        settings = request.app.state.settings if hasattr(request.app.state, "settings") else None
    except Exception:
        settings = None

    providers: List[Dict[str, Any]] = [
        {"id": "openai", "name": "OpenAI", "type": "llm", "docs_url": "https://platform.openai.com/docs"},
        {"id": "firecrawl", "name": "Firecrawl", "type": "crawler", "docs_url": "https://www.firecrawl.dev/docs"},
        {"id": "neo4j", "name": "Neo4j", "type": "graph-db", "docs_url": "https://neo4j.com/docs/"},
        {"id": "local-embeddings", "name": "Local Embeddings", "type": "embedding", "docs_url": "https://github.com/SuTang-vain/OpenShrimp"}
    ]

    return {"providers": providers}


@router.post("/services/credentials")
async def save_credentials(input: CredentialsInput):
    if not input.provider_id or not input.credentials:
        raise HTTPException(status_code=400, detail="provider_id 与 credentials 不能为空")
    ok = save_credentials(input.provider_id, input.credentials)
    if not ok:
        raise HTTPException(status_code=500, detail="凭据保存失败")

    return {"ok": True, "provider_id": input.provider_id}


@router.get("/services/test")
async def test_connectivity(provider_id: str):
    creds = load_credentials(provider_id) or {}

    status = {"provider_id": provider_id, "reachable": False, "message": ""}

    if provider_id == "openai":
        api_key = creds.get("api_key") or os.getenv("OPENAI_API_KEY")
        status["reachable"] = bool(api_key)
        status["message"] = "检测到 API Key" if api_key else "未配置 API Key"
    elif provider_id == "neo4j":
        # Aura: neo4j+s URL；本地：bolt://localhost:7687
        url = creds.get("connectionUrl") or os.getenv("NEO4J_URL")
        user = creds.get("username") or os.getenv("NEO4J_USER")
        pwd = creds.get("password") or os.getenv("NEO4J_PASSWORD")
        db = creds.get("database") or os.getenv("NEO4J_DATABASE") or "neo4j"
        if not (url and user and pwd):
            status["message"] = "缺少 connectionUrl/username/password"
        else:
            try:
                client = Neo4jClient(url, user, pwd, db)
                client.verify_connectivity()
                client.ensure_schema()
                client.close()
                status["reachable"] = True
                status["message"] = f"连通性正常：{url} / db={db}"
            except Exception as e:
                status["message"] = f"连接失败：{e}"
    else:
        status["message"] = "MVP 暂未实现深度连通性测试"

    return status