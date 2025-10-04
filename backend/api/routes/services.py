import os
import socket
from typing import Dict, Any, List

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from backend.shared.secure_store import load_credentials, save_credentials
from backend.infrastructure.graph.neo4j_client import Neo4jClient
from backend.shared.utils.response import APIResponse
from urllib.parse import urlparse


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
        {"id": "modelscope", "name": "ModelScope", "type": "llm", "docs_url": "https://modelscope.cn"},
        {"id": "zhipu-ai", "name": "智谱AI (GLM)", "type": "llm", "docs_url": "https://open.bigmodel.cn"},
        {"id": "deepseek", "name": "DeepSeek", "type": "llm", "docs_url": "https://platform.deepseek.com"},
        {"id": "firecrawl", "name": "Firecrawl", "type": "crawler", "docs_url": "https://www.firecrawl.dev/docs"},
        {"id": "neo4j", "name": "Neo4j", "type": "graph-db", "docs_url": "https://neo4j.com/docs/"},
        {"id": "ollama", "name": "Ollama", "type": "local-model", "docs_url": "https://ollama.ai"},
        {"id": "lm-studio", "name": "LM Studio", "type": "local-model", "docs_url": "https://lmstudio.ai"},
        {"id": "local-embeddings", "name": "Local Embeddings", "type": "embedding", "docs_url": "https://github.com/SuTang-vain/OpenShrimp"}
    ]

    return {"providers": providers}


@router.post("/services/credentials")
async def save_credentials_route(input: CredentialsInput):
    if not input.provider_id or not input.credentials:
        return APIResponse.error(message="provider_id 与 credentials 不能为空", status_code=400)
    ok = save_credentials(input.provider_id, input.credentials)
    if not ok:
        return APIResponse.error(message="凭据保存失败", status_code=500)

    return APIResponse.success(data={"saved": True, "provider_id": input.provider_id}, message="凭据已保存")


@router.get("/services/test")
async def test_connectivity(provider_id: str):
    creds = load_credentials(provider_id) or {}

    status = {"provider_id": provider_id, "reachable": False, "message": ""}

    if provider_id == "openai":
        api_key = creds.get("api_key") or os.getenv("OPENAI_API_KEY")
        status["reachable"] = bool(api_key)
        status["message"] = "检测到 API Key" if api_key else "未配置 API Key"
    elif provider_id == "modelscope":
        # 轻量连通性测试（不做真实推理调用）：检测关键字段是否已配置
        api_key = creds.get("apiKey") or creds.get("api_key") or os.getenv("MODELSCOPE_SDK_TOKEN")
        base_url = creds.get("baseUrl") or os.getenv("MODELSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/api/v1")
        if not api_key:
            status["message"] = "未配置 API Key"
        else:
            status["reachable"] = True
            status["message"] = f"已配置 API Key，BaseURL={base_url}"
    elif provider_id == "zhipu-ai":
        api_key = creds.get("apiKey") or creds.get("api_key") or os.getenv("ZHIPU_API_KEY")
        base_url = creds.get("baseUrl") or os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
        if not api_key:
            status["message"] = "未配置 API Key"
        else:
            status["reachable"] = True
            status["message"] = f"已配置 API Key，BaseURL={base_url}"
    elif provider_id == "deepseek":
        api_key = creds.get("apiKey") or creds.get("api_key") or os.getenv("DEEPSEEK_API_KEY")
        base_url = creds.get("baseUrl") or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        if not api_key:
            status["message"] = "未配置 API Key"
        else:
            status["reachable"] = True
            status["message"] = f"已配置 API Key，BaseURL={base_url}"
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
    elif provider_id == "firecrawl":
        api_key = creds.get("apiKey") or creds.get("api_key") or os.getenv("FIRECRAWL_API_KEY")
        base_url = creds.get("baseUrl") or os.getenv("FIRECRAWL_BASE_URL", "https://api.firecrawl.dev")
        if not api_key:
            status["message"] = "未配置 API Key"
        else:
            status["reachable"] = True
            status["message"] = f"已配置 API Key，BaseURL={base_url}"
    elif provider_id == "ollama":
        base_url = creds.get("baseUrl") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        parsed = urlparse(base_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (11434 if parsed.scheme in ("http", "https") else 11434)
        try:
            with socket.create_connection((host, port), timeout=2):
                status["reachable"] = True
                status["message"] = f"端口可达：{host}:{port}，BaseURL={base_url}"
        except Exception as e:
            status["message"] = f"无法连接本地端口 {host}:{port}，请确认服务已启动：{e}"
    elif provider_id == "lm-studio":
        base_url = creds.get("baseUrl") or os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
        parsed = urlparse(base_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (1234 if parsed.scheme in ("http", "https") else 1234)
        try:
            with socket.create_connection((host, port), timeout=2):
                status["reachable"] = True
                status["message"] = f"端口可达：{host}:{port}，BaseURL={base_url}"
        except Exception as e:
            status["message"] = f"无法连接本地端口 {host}:{port}，请确认服务已启动：{e}"
    else:
        status["message"] = "MVP 暂未实现深度连通性测试"

    return status