from fastapi import APIRouter
from pydantic import BaseModel
import os


router = APIRouter(prefix="/mcp", tags=["MCP"])


class MCPInfo(BaseModel):
    service_name: str
    version: str
    base_url: str
    environment: str | None = None


class Capability(BaseModel):
    key: str
    description: str
    available: bool


class CapabilitiesResponse(BaseModel):
    service: MCPInfo
    capabilities: list[Capability]


@router.get("/info", response_model=MCPInfo)
def get_mcp_info() -> MCPInfo:
    base_url = os.getenv("MCP_BASE_URL", "http://127.0.0.1:8000/api")
    version = os.getenv("MCP_VERSION", "0.1.0")
    env = os.getenv("ENVIRONMENT", "dev")
    return MCPInfo(
        service_name="shrimp-agent-v2",
        version=version,
        base_url=base_url,
        environment=env,
    )


@router.get("/capabilities", response_model=CapabilitiesResponse)
def get_mcp_capabilities() -> CapabilitiesResponse:
    info = get_mcp_info()
    capabilities = [
        Capability(key="rag.query", description="RAG 查询接口 /api/query", available=True),
        Capability(key="documents.upload", description="文档上传接口 /api/documents/upload", available=True),
        Capability(key="rag.embedding.switch", description="嵌入模型热切换 /api/rag/embedding/switch", available=True),
        Capability(key="rag.stats", description="RAG 统计查看 /api/rag/stats", available=True),
        Capability(key="graph.build", description="构建知识图谱 /api/graph/build（内存/Neo4j）", available=True),
        Capability(key="graph.query", description="图查询 /api/graph/query（邻居/最短路径/术语子图）", available=True),
        Capability(key="services.credentials", description="服务密钥管理（计划）", available=False),
    ]
    return CapabilitiesResponse(service=info, capabilities=capabilities)