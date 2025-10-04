#!/usr/bin/env python3
"""
智能体API路由
提供智能体相关的API端点

运行环境: Python 3.11+
依赖: fastapi, typing
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, Field

from backend.api.dependencies.auth import get_current_user, require_api_key
from backend.api.dependencies.services import get_agent_service, get_camel_service, get_rag_engine, get_llm_manager
from backend.services.agent.camel_service import CamelAgentService
from backend.shared.utils.response import create_success_response, create_error_response
from backend.services.agent.manager import AgentServiceManager, AgentTask
from backend.core.llm import LLMManager, LLMRequest

# 创建路由器
router = APIRouter()


# 请求模型
class AgentTaskRequest(BaseModel):
    """智能体任务请求"""
    agent_type: str = Field(..., description="智能体类型")
    input_data: Dict[str, Any] = Field(..., description="输入数据")
    priority: str = Field(default="normal", description="任务优先级")
    timeout: Optional[float] = Field(default=None, description="超时时间（秒）")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class AgentTaskResponse(BaseModel):
    """智能体任务响应"""
    task_id: str
    agent_type: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AgentStatsResponse(BaseModel):
    """智能体统计响应"""
    active_tasks: int
    completed_tasks: int
    max_concurrent_tasks: int
    task_status_breakdown: Dict[str, int]


class CamelSearchRequest(BaseModel):
    """CAMEL 搜索请求模型"""
    query: str = Field(..., description="搜索查询")
    search_type: Optional[str] = Field(default="web", description="搜索类型：web 或 document")
    max_results: Optional[int] = Field(default=10, description="最大返回数量")
    ingest_to_rag: bool = Field(default=True, description="是否将结果入库到RAG")


class GraphRAGRequest(BaseModel):
    """基于图谱上下文的问答请求"""
    query: str = Field(..., description="用户问题或查询")
    top_k: int = Field(default=6, description="术语提取数量与检索片段数量")
    depth: int = Field(default=1, description="图邻居检索深度")
    mode: str = Field(default="neighbors", description="neighbors 或 shortest")
    shortest_a: Optional[str] = Field(default=None, description="最短路径起点")
    shortest_b: Optional[str] = Field(default=None, description="最短路径终点")
    max_context_tokens: int = Field(default=1200, description="拼接到提示中的最大上下文长度")


def _extract_terms(text: str) -> List[str]:
    """简化术语抽取：中文2+字词、英文3+字符词，按频次排序"""
    if not text:
        return []
    import re
    zh_words = re.findall(r"[\u4e00-\u9fa5]{2,}", text)
    en_words = re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", text)
    words = zh_words + [w.lower() for w in en_words]
    freq: Dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    filtered = [w for w, c in freq.items() if c >= 1]
    return sorted(filtered, key=lambda w: freq[w], reverse=True)


def _summarize_graph(graph: Dict[str, Any], max_len: int = 1200) -> str:
    """将图节点与边压缩为文本片段用于提示上下文"""
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    lines: List[str] = []
    if nodes:
        lines.append("[图节点]")
        for n in nodes[:30]:
            label = n.get("label") or n.get("id")
            lines.append(f"- {label}")
    if edges:
        lines.append("[图关系]")
        for e in edges[:60]:
            t = e.get("type", "relates")
            lines.append(f"- {e.get('source')} -({t})-> {e.get('target')}")
    text = "\n".join(lines)
    return text[:max_len]


# API端点
@router.post("/tasks", response_model=Dict[str, Any])
async def create_agent_task(
    request: AgentTaskRequest,
    background_tasks: BackgroundTasks,
    agent_service: AgentServiceManager = Depends(get_agent_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """创建智能体任务
    
    Args:
        request: 任务请求
        background_tasks: 后台任务
        agent_service: 智能体服务
        current_user: 当前用户
        
    Returns:
        任务创建响应
    """
    try:
        # 验证智能体类型
        valid_agent_types = ["search", "analysis", "extraction", "generation"]
        if request.agent_type not in valid_agent_types:
            return create_error_response(
                message=f"不支持的智能体类型: {request.agent_type}",
                code=400,
                error_code="INVALID_AGENT_TYPE"
            )
        
        # 创建任务
        task_id = await agent_service.create_task(
            agent_type=request.agent_type,
            input_data=request.input_data
        )
        
        return create_success_response(
            data={"task_id": task_id},
            message="智能体任务创建成功"
        )
        
    except Exception as e:
        return create_error_response(
            message=f"创建智能体任务失败: {str(e)}",
            code=500
        )


@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_agent_task(
    task_id: str,
    agent_service: AgentServiceManager = Depends(get_agent_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """获取智能体任务状态
    
    Args:
        task_id: 任务ID
        agent_service: 智能体服务
        current_user: 当前用户
        
    Returns:
        任务状态响应
    """
    try:
        task = await agent_service.get_task_status(task_id)
        
        if not task:
            return create_error_response(
                message=f"任务不存在: {task_id}",
                code=404,
                error_code="TASK_NOT_FOUND"
            )
        
        task_data = {
            "task_id": task.task_id,
            "agent_type": task.agent_type,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result": task.result,
            "error": task.error
        }
        
        return create_success_response(
            data=task_data,
            message="获取任务状态成功"
        )
        
    except Exception as e:
        return create_error_response(
            message=f"获取任务状态失败: {str(e)}",
            code=500
        )


@router.delete("/tasks/{task_id}", response_model=Dict[str, Any])
async def cancel_agent_task(
    task_id: str,
    agent_service: AgentServiceManager = Depends(get_agent_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """取消智能体任务
    
    Args:
        task_id: 任务ID
        agent_service: 智能体服务
        current_user: 当前用户
        
    Returns:
        取消任务响应
    """
    try:
        success = await agent_service.cancel_task(task_id)
        
        if not success:
            return create_error_response(
                message=f"无法取消任务: {task_id}",
                code=400,
                error_code="TASK_CANCEL_FAILED"
            )
        
        return create_success_response(
            data={"task_id": task_id},
            message="任务取消成功"
        )
        
    except Exception as e:
        return create_error_response(
            message=f"取消任务失败: {str(e)}",
            code=500
        )


@router.get("/tasks", response_model=Dict[str, Any])
async def list_agent_tasks(
    status: Optional[str] = None,
    limit: int = 50,
    agent_service: AgentServiceManager = Depends(get_agent_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """列出智能体任务
    
    Args:
        status: 状态过滤（可选）
        limit: 返回数量限制
        agent_service: 智能体服务
        current_user: 当前用户
        
    Returns:
        任务列表响应
    """
    try:
        if status == "active":
            tasks = await agent_service.list_active_tasks()
        elif status == "completed":
            tasks = await agent_service.list_completed_tasks(limit=limit)
        else:
            # 获取所有任务
            active_tasks = await agent_service.list_active_tasks()
            completed_tasks = await agent_service.list_completed_tasks(limit=limit//2)
            tasks = active_tasks + completed_tasks
        
        # 转换为响应格式
        task_list = []
        for task in tasks[:limit]:
            task_data = {
                "task_id": task.task_id,
                "agent_type": task.agent_type,
                "status": task.status,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "has_result": task.result is not None,
                "has_error": task.error is not None
            }
            task_list.append(task_data)
        
        return create_success_response(
            data={
                "tasks": task_list,
                "total": len(task_list),
                "filter": status
            },
            message="获取任务列表成功"
        )
        
    except Exception as e:
        return create_error_response(
            message=f"获取任务列表失败: {str(e)}",
            code=500
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_agent_stats(
    agent_service: AgentServiceManager = Depends(get_agent_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """获取智能体统计信息
    
    Args:
        agent_service: 智能体服务
        current_user: 当前用户
        
    Returns:
        统计信息响应
    """
    try:
        stats = agent_service.get_statistics()
        
        return create_success_response(
            data=stats,
            message="获取统计信息成功"
        )
        
    except Exception as e:
        return create_error_response(
            message=f"获取统计信息失败: {str(e)}",
            code=500
        )


@router.post("/camel/search", response_model=Dict[str, Any])
async def camel_search(
    request: CamelSearchRequest,
    camel_service: CamelAgentService = Depends(get_camel_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """执行 CAMEL 搜索并可选入库到 RAG
    
    Args:
        request: CAMEL 搜索请求
        camel_service: CAMEL 服务
        current_user: 当前用户
        
    Returns:
        搜索结果
    """
    try:
        result = await camel_service.search(
            query=request.query,
            search_type=request.search_type or 'web',
            max_results=request.max_results,
            ingest_to_rag=request.ingest_to_rag
        )
        return create_success_response(
            data=result,
            message="CAMEL 搜索完成"
        )
    except HTTPException as e:
        # 依赖不可用等
        return create_error_response(
            message=f"CAMEL服务不可用: {e.detail}",
            code=e.status_code
        )
    except Exception as e:
        return create_error_response(
            message=f"CAMEL 搜索失败: {str(e)}",
            code=500
        )


@router.post("/graph-rag", response_model=Dict[str, Any])
async def graph_rag_qa(
    request_body: GraphRAGRequest,
    request: Request,
    rag_engine = Depends(get_rag_engine),
    llm_manager: LLMManager = Depends(get_llm_manager),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """基于图谱上下文的问答（MVP）

    - 从 ContextGraph 获取与查询相关的子图（邻居或最短路径）
    - 结合 RAG 检索片段，拼接上下文
    - 调用 LLM 生成中文回答
    """
    try:
        services = getattr(request.state, "services", {})
        context_graph = services.get("context_graph")

        # 图谱上下文构建
        graph: Dict[str, Any] = {"nodes": [], "edges": []}
        source = "none"
        if context_graph:
            try:
                if request_body.mode.lower() == "shortest" and request_body.shortest_a and request_body.shortest_b:
                    graph = context_graph.shortest_path(
                        request_body.shortest_a,
                        request_body.shortest_b,
                        max_hops=request_body.depth
                    )
                    source = "context-graph-shortest"
                else:
                    terms = _extract_terms(request_body.query)[: request_body.top_k]
                    graph = context_graph.query_neighbors(
                        terms,
                        depth=request_body.depth,
                        limit=max(20, request_body.top_k * 10)
                    )
                    source = "context-graph-neighbors"
            except Exception:
                # 保持空图，后续用文本上下文兜底
                pass

        graph_context_text = _summarize_graph(graph, max_len=request_body.max_context_tokens)

        # RAG 检索片段
        retrieved_snippets: List[str] = []
        try:
            RetrievalQuery = rag_engine.get_retrieval_query_cls()
            RetrievalStrategy = rag_engine.get_retrieval_strategy_enum()
            rq = RetrievalQuery(query=request_body.query, top_k=request_body.top_k, strategy=RetrievalStrategy.SIMILARITY)
            results = await rag_engine.retriever.retrieve(rq)
            for r in results:
                text = r.get("text") if isinstance(r, dict) else getattr(getattr(r, "chunk", None), "content", "")
                if text:
                    retrieved_snippets.append(str(text))
        except Exception:
            # RAG 不可用或失败时忽略
            pass

        # 术语作为额外上下文关键词
        terms = _extract_terms(request_body.query)[: request_body.top_k]

        # 构建提示词
        snippets_text = "\n\n".join([s[:300] for s in retrieved_snippets[:5]])
        prompt = (
            "你是一个知识密集型助理。请结合提供的图谱上下文与检索片段，"
            "准确、简洁地回答用户问题。若信息不足请明确说明，不要编造。"
            "\n\n[用户问题]\n" + request_body.query +
            "\n\n[关键术语]\n- " + "\n- ".join(terms) +
            ("\n\n[图谱上下文]\n" + graph_context_text if graph_context_text else "") +
            ("\n\n[检索片段]\n" + snippets_text if snippets_text else "") +
            "\n\n请用中文作答，结构化给出要点。"
        )

        # 调用 LLM
        llm_req = LLMRequest(prompt=prompt, max_tokens=700, temperature=0.3)
        llm_res = await llm_manager.generate(llm_req)

        if getattr(llm_res, "error", None):
            return create_error_response(
                message=f"LLM生成失败: {llm_res.error}",
                code=500
            )

        return create_success_response(
            data={
                "answer": llm_res.content,
                "graph_source": source,
                "graph": graph,
                "terms": terms,
                "retrieved_count": len(retrieved_snippets)
            },
            message="GraphRAG 问答完成"
        )

    except HTTPException as e:
        return create_error_response(message=e.detail, code=e.status_code)
    except Exception as e:
        return create_error_response(message=f"GraphRAG 问答失败: {str(e)}", code=500)


@router.get("/types", response_model=Dict[str, Any])
async def get_agent_types(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """获取支持的智能体类型
    
    Args:
        current_user: 当前用户
        
    Returns:
        智能体类型列表
    """
    try:
        agent_types = [
            {
                "type": "search",
                "name": "搜索智能体",
                "description": "执行搜索任务，从多个数据源获取信息",
                "input_schema": {
                    "query": "搜索查询字符串",
                    "sources": "搜索源列表（可选）",
                    "max_results": "最大结果数量（可选）"
                }
            },
            {
                "type": "analysis",
                "name": "分析智能体",
                "description": "分析文本内容，提取关键信息和洞察",
                "input_schema": {
                    "content": "待分析的文本内容",
                    "analysis_type": "分析类型（sentiment/keywords/summary）"
                }
            },
            {
                "type": "extraction",
                "name": "提取智能体",
                "description": "从网页或文档中提取结构化信息",
                "input_schema": {
                    "url": "网页URL或文档路径",
                    "extraction_rules": "提取规则（可选）"
                }
            },
            {
                "type": "generation",
                "name": "生成智能体",
                "description": "基于输入生成文本内容",
                "input_schema": {
                    "prompt": "生成提示",
                    "style": "生成风格（可选）",
                    "max_length": "最大长度（可选）"
                }
            }
        ]
        
        return create_success_response(
            data={"agent_types": agent_types},
            message="获取智能体类型成功"
        )
        
    except Exception as e:
        return create_error_response(
            message=f"获取智能体类型失败: {str(e)}",
            code=500
        )


@router.post("/batch", response_model=Dict[str, Any])
async def create_batch_tasks(
    requests: List[AgentTaskRequest],
    background_tasks: BackgroundTasks,
    agent_service: AgentServiceManager = Depends(get_agent_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """批量创建智能体任务
    
    Args:
        requests: 任务请求列表
        background_tasks: 后台任务
        agent_service: 智能体服务
        current_user: 当前用户
        
    Returns:
        批量任务创建响应
    """
    try:
        if len(requests) > 10:
            return create_error_response(
                message="批量任务数量不能超过10个",
                code=400,
                error_code="BATCH_SIZE_EXCEEDED"
            )
        
        task_ids = []
        errors = []
        
        for i, request in enumerate(requests):
            try:
                task_id = await agent_service.create_task(
                    agent_type=request.agent_type,
                    input_data=request.input_data
                )
                task_ids.append(task_id)
            except Exception as e:
                errors.append({
                    "index": i,
                    "error": str(e)
                })
        
        return create_success_response(
            data={
                "task_ids": task_ids,
                "created_count": len(task_ids),
                "error_count": len(errors),
                "errors": errors
            },
            message=f"批量创建任务完成，成功: {len(task_ids)}, 失败: {len(errors)}"
        )
        
    except Exception as e:
        return create_error_response(
            message=f"批量创建任务失败: {str(e)}",
            code=500
        )