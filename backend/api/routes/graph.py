from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import re
from backend.infrastructure.graph.neo4j_client import Neo4jClient


router = APIRouter()


class GraphBuildInput(BaseModel):
    text: str | None = None
    documents: List[Dict[str, Any]] | None = None
    source_id: str | None = None
    max_nodes: int = 40


class GraphQueryInput(BaseModel):
    query: str
    top_k: int = 8
    max_nodes: int = 40
    # 查询增强参数
    relation_types: Optional[List[str]] = None
    depth: int = 1  # k-hop 深度或最短路径最大跳数
    mode: str = "neighbors"  # neighbors | shortest
    shortest_a: Optional[str] = None
    shortest_b: Optional[str] = None


def _extract_terms(text: str) -> List[str]:
    """非常简化的术语抽取，兼容中英文。
    - 中文：抽取长度>=2的连续汉字词，按频次排序
    - 英文：抽取长度>=3的字母数字词，按频次排序
    """
    if not text:
        return []

    # 中文与英文混合分词（简化版）
    zh_words = re.findall(r"[\u4e00-\u9fa5]{2,}", text)
    en_words = re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", text)
    words = zh_words + [w.lower() for w in en_words]

    freq: Dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    # 过滤过短或低频
    filtered = [w for w, c in freq.items() if c >= 1]
    # 频次排序
    return sorted(filtered, key=lambda w: freq[w], reverse=True)


def _build_graph_from_sentences(sentences: List[str], max_nodes: int = 40):
    # 收集术语
    all_terms: List[str] = []
    for s in sentences:
        all_terms.extend(_extract_terms(s))

    # 限制节点数量
    unique_terms: List[str] = []
    for t in all_terms:
        if t not in unique_terms:
            unique_terms.append(t)
        if len(unique_terms) >= max_nodes:
            break

    # 构造节点
    nodes = [
        {
            "id": term,
            "label": term,
            "weight": 1
        }
        for term in unique_terms
    ]

    # 边：同句共现视为关联
    edges = []
    evidence = []
    for s in sentences:
        terms = [t for t in _extract_terms(s) if t in unique_terms]
        for i in range(len(terms)):
            for j in range(i + 1, len(terms)):
                edges.append({
                    "source": terms[i],
                    "target": terms[j],
                    "weight": 1,
                    "type": "cooccurrence"
                })
        if terms:
            evidence.append({
                "fragment": s.strip(),
                "terms": terms
            })

    # 去重边
    seen = set()
    dedup_edges = []
    for e in edges:
        key = (min(e["source"], e["target"]), max(e["source"], e["target"]))
        if key in seen:
            continue
        seen.add(key)
        dedup_edges.append(e)

    return {
        "nodes": nodes,
        "edges": dedup_edges,
        "evidence": evidence
    }


def _extract_entities_relations(sentences: List[str]) -> Dict[str, Any]:
    """MVP 实体/关系抽取：
    - 实体：基于术语抽取的候选，按频次选前 max_nodes
    - 关系：同句共现的术语对，类型标记为 CO_OCCURS
    """
    term_freq: Dict[str, int] = {}
    relations: List[Dict[str, Any]] = []
    for s in sentences:
        terms = _extract_terms(s)
        for t in terms:
            term_freq[t] = term_freq.get(t, 0) + 1
        for i in range(len(terms)):
            for j in range(i + 1, len(terms)):
                relations.append({
                    "source": terms[i],
                    "target": terms[j],
                    "type": "CO_OCCURS"
                })

    # 实体集
    entities = [{"name": t, "type": "term"} for t, _ in sorted(term_freq.items(), key=lambda kv: kv[1], reverse=True)]
    return {"entities": entities, "relations": relations}


@router.post("/graph/build")
async def graph_build(input: GraphBuildInput, request: Request):
    services = getattr(request.state, "services", {})
    rag_engine = services.get("rag_engine")
    if not rag_engine:
        raise HTTPException(status_code=500, detail="RAG 引擎未初始化")

    sentences: List[str] = []

    if input.text:
        sentences = re.split(r"[。！？.!?]\s*", input.text)
    elif input.documents:
        for d in input.documents:
            content = d.get("content") or d.get("text") or ""
            if content:
                sentences.extend(re.split(r"[。！？.!?]\s*", content))
    else:
        raise HTTPException(status_code=400, detail="必须提供 text 或 documents 字段")

    graph = _build_graph_from_sentences(sentences, max_nodes=input.max_nodes)

    # 尝试写入 Neo4j（若凭据已配置）
    graph_db = services.get("graph_db")
    if graph_db is None:
        # 懒加载：从凭据存储创建
        graph_db = Neo4jClient.from_store()
        if graph_db:
            services["graph_db"] = graph_db

    if graph_db:
        try:
            terms = [n["label"] for n in graph["nodes"]]
            graph_db.upsert_terms(terms)
            graph_db.upsert_source(input.source_id)
            for e in graph["edges"]:
                graph_db.add_cooccurrence(e["source"], e["target"], input.source_id)

            # 新增：实体与关系抽取并持久化
            er = _extract_entities_relations(sentences)
            for ent in er.get("entities", [])[: input.max_nodes]:
                graph_db.upsert_entity(ent.get("name"), ent.get("type"))
            for rel in er.get("relations", []):
                graph_db.add_relation(rel.get("source"), rel.get("type"), rel.get("target"), input.source_id)
        except Exception as e:
            # 不中断请求，返回警告信息
            return {
                "graph": graph,
                "source_id": input.source_id,
                "warning": f"Neo4j 写入失败: {e}"
            }

    return {
        "graph": graph,
        "source_id": input.source_id
    }


@router.post("/graph/query")
async def graph_query(input: GraphQueryInput, request: Request):
    services = getattr(request.state, "services", {})
    rag_engine = services.get("rag_engine")
    if not rag_engine:
        raise HTTPException(status_code=500, detail="RAG 引擎未初始化")

    # 通过 RAG 检索相关片段
    try:
        RetrievalQuery = rag_engine.get_retrieval_query_cls()
        RetrievalStrategy = rag_engine.get_retrieval_strategy_enum()
    except Exception:
        RetrievalQuery = None
        RetrievalStrategy = None

    sentences: List[str] = []
    if RetrievalQuery and RetrievalStrategy:
        try:
            q = RetrievalQuery(query=input.query, top_k=input.top_k, strategy=RetrievalStrategy.SIMILARITY)
            results = await rag_engine.retriever.retrieve(q)
            for r in results:
                text = r.get("text") or r.get("content") or ""
                if text:
                    sentences.extend(re.split(r"[。！？.!?]\s*", text))
        except Exception:
            # 回退：直接用查询词
            sentences = [input.query]
    else:
        sentences = [input.query]

    # 优先使用 Neo4j 图查询
    graph_db = services.get("graph_db")
    if graph_db is None:
        graph_db = Neo4jClient.from_store()
        if graph_db:
            services["graph_db"] = graph_db

    if graph_db:
        try:
            # 最近邻或最短路径查询（实体关系图）
            if input.mode.lower() == "shortest" and input.shortest_a and input.shortest_b:
                graph = graph_db.shortest_path(input.shortest_a, input.shortest_b, max_hops=input.depth, relation_types=input.relation_types)
                return {"graph": graph, "query": input.query, "source": "neo4j-shortest"}
            else:
                terms = _extract_terms(input.query)[: input.top_k]
                graph = graph_db.query_neighbors(terms, relation_types=input.relation_types, depth=input.depth, limit=input.max_nodes)
                return {"graph": graph, "query": input.query, "source": "neo4j-neighbors"}
        except Exception:
            # 回退到术语子图查询
            try:
                terms = _extract_terms(input.query)[: input.top_k]
                graph = graph_db.query_subgraph_by_terms(terms, limit=input.max_nodes)
                return {"graph": graph, "query": input.query, "source": "neo4j-terms"}
            except Exception:
                pass

    # 回退到内存共现图
    graph = _build_graph_from_sentences(sentences, max_nodes=input.max_nodes)
    return {
        "graph": graph,
        "query": input.query,
        "source": "fallback"
    }