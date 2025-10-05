from fastapi import APIRouter, Depends
from backend.api.routes.search import rag_query_stream, rag_query
from backend.api.schemas.search import RAGQueryRequest, RAGStatsResponse, RAGQueryResponse
from backend.core.auth import get_current_user

router = APIRouter(prefix="/mcp/rag", tags=["MCP-RAG"])

@router.post("/retrieve", response_model=RAGQueryResponse)
async def mcp_rag_retrieve(
    payload: RAGQueryRequest,
    user: dict = Depends(get_current_user),
):
    if payload.stream:
        result = await rag_query_stream(payload, user)
    else:
        result = await rag_query(payload, user)
    return result

@router.get("/stats", response_model=RAGStatsResponse)
async def mcp_rag_stats(user: dict = Depends(get_current_user)):
    from backend.api.routes.search import rag_stats
    return await rag_stats(user)
