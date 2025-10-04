#!/usr/bin/env python3
"""
内存图谱存储（MVP）
用于阶段一 ContextGraph MCP 的快速落地：
- 维护节点与边的简单结构
- 支持术语子图检索、邻居扩展、最短路径

运行环境: Python 3.11+
依赖: 无（仅标准库）
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, Set, Tuple
import re


class MemoryGraphStore:
    def __init__(self) -> None:
        self.nodes: Dict[str, Dict[str, Any]] = {}
        # 无向边，用排序后的二元组唯一标识，保留属性
        self.edges: Dict[Tuple[str, str], Dict[str, Any]] = {}

    # 基础操作
    def add_node(self, node_id: str, label: Optional[str] = None, **props: Any) -> None:
        if not node_id:
            return
        self.nodes[node_id] = {
            "id": node_id,
            "label": label or node_id,
            **props,
        }

    def update_node(self, node_id: str, data: Dict[str, Any]) -> None:
        if node_id in self.nodes:
            self.nodes[node_id].update(data)

    def add_edge(self, source: str, target: str, *, edge_type: str = "relates", weight: float = 1.0) -> None:
        if not source or not target or source == target:
            return
        key = self._edge_key(source, target)
        self.edges[key] = {
            "source": source,
            "target": target,
            "type": edge_type,
            "weight": weight,
        }

    def upsert_terms(self, terms: List[str]) -> None:
        for t in terms:
            self.add_node(t, label=t)

    # 导入辅助
    def ingest_graph(self, graph: Dict[str, Any]) -> None:
        for n in graph.get("nodes", []):
            self.add_node(str(n.get("id")), label=n.get("label"), weight=n.get("weight", 1))
        for e in graph.get("edges", []):
            self.add_edge(str(e.get("source")), str(e.get("target")), edge_type=e.get("type", "relates"), weight=e.get("weight", 1.0))

    def ingest_text(self, text: str, max_nodes: int = 40) -> Dict[str, Any]:
        sentences = re.split(r"[。！？.!?]\s*", text or "")
        graph = self._build_graph_from_sentences(sentences, max_nodes=max_nodes)
        self.ingest_graph(graph)
        return graph

    # 查询接口
    def query_subgraph_by_terms(self, terms: List[str], limit: int = 40) -> Dict[str, Any]:
        terms_set: Set[str] = set(terms or [])
        nodes = [self.nodes[t] for t in terms if t in self.nodes][:limit]

        edges: List[Dict[str, Any]] = []
        for (a, b), e in self.edges.items():
            if a in terms_set and b in terms_set:
                edges.append(e)
                if len(edges) >= limit:
                    break

        return {"nodes": nodes, "edges": edges}

    def query_neighbors(self, terms: List[str], depth: int = 1, limit: int = 40, relation_types: Optional[List[str]] = None) -> Dict[str, Any]:
        start: Set[str] = set([t for t in terms if t in self.nodes])
        visited: Set[str] = set()
        frontier: Set[str] = set(start)

        def _neighbors(node_id: str) -> List[str]:
            ns = []
            for (a, b), e in self.edges.items():
                if relation_types and e.get("type") not in set(relation_types):
                    continue
                if a == node_id:
                    ns.append(b)
                elif b == node_id:
                    ns.append(a)
            return ns

        for _ in range(max(1, depth)):
            next_frontier: Set[str] = set()
            for nid in frontier:
                if nid in visited:
                    continue
                visited.add(nid)
                for nb in _neighbors(nid):
                    if nb not in visited:
                        next_frontier.add(nb)
            frontier = next_frontier

        result_nodes: List[Dict[str, Any]] = []
        result_edges: List[Dict[str, Any]] = []
        keep: Set[str] = set(list(start) + list(visited))
        for nid in keep:
            if nid in self.nodes:
                result_nodes.append(self.nodes[nid])
                if len(result_nodes) >= limit:
                    break

        for (a, b), e in self.edges.items():
            if a in keep and b in keep:
                result_edges.append(e)
                if len(result_edges) >= limit:
                    break

        return {"nodes": result_nodes, "edges": result_edges}

    def shortest_path(self, a: str, b: str, max_hops: int = 3, relation_types: Optional[List[str]] = None) -> Dict[str, Any]:
        # 简化版 BFS
        if a not in self.nodes or b not in self.nodes:
            return {"nodes": [], "edges": []}

        from collections import deque
        queue = deque([(a, [a])])
        visited: Set[str] = set()

        def _neighbors(node_id: str) -> List[str]:
            ns = []
            for (x, y), e in self.edges.items():
                if relation_types and e.get("type") not in set(relation_types):
                    continue
                if x == node_id:
                    ns.append(y)
                elif y == node_id:
                    ns.append(x)
            return ns

        while queue:
            cur, path = queue.popleft()
            if cur == b:
                # 构造子图
                nodes = [self.nodes[n] for n in path if n in self.nodes]
                edges: List[Dict[str, Any]] = []
                for i in range(len(path) - 1):
                    key = self._edge_key(path[i], path[i + 1])
                    e = self.edges.get(key)
                    if e:
                        edges.append(e)
                return {"nodes": nodes, "edges": edges}
            if len(path) - 1 >= max_hops:
                continue
            if cur in visited:
                continue
            visited.add(cur)
            for nb in _neighbors(cur):
                if nb not in visited:
                    queue.append((nb, path + [nb]))

        return {"nodes": [], "edges": []}

    # 简化术语抽取与共现图构建（与现有路由中逻辑一致）
    @staticmethod
    def _extract_terms(text: str) -> List[str]:
        if not text:
            return []
        zh_words = re.findall(r"[\u4e00-\u9fa5]{2,}", text)
        en_words = re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", text)
        words = zh_words + [w.lower() for w in en_words]
        freq: Dict[str, int] = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        filtered = [w for w, c in freq.items() if c >= 1]
        return sorted(filtered, key=lambda w: freq[w], reverse=True)

    def _build_graph_from_sentences(self, sentences: List[str], max_nodes: int = 40) -> Dict[str, Any]:
        all_terms: List[str] = []
        for s in sentences:
            all_terms.extend(self._extract_terms(s))

        unique_terms: List[str] = []
        for t in all_terms:
            if t not in unique_terms:
                unique_terms.append(t)
            if len(unique_terms) >= max_nodes:
                break

        nodes = [{"id": term, "label": term, "weight": 1} for term in unique_terms]

        edges: List[Dict[str, Any]] = []
        for s in sentences:
            terms = [t for t in self._extract_terms(s) if t in unique_terms]
            for i in range(len(terms)):
                for j in range(i + 1, len(terms)):
                    edges.append({
                        "source": terms[i],
                        "target": terms[j],
                        "weight": 1,
                        "type": "cooccurrence",
                    })

        seen: Set[Tuple[str, str]] = set()
        dedup_edges: List[Dict[str, Any]] = []
        for e in edges:
            key = self._edge_key(e["source"], e["target"]) 
            if key in seen:
                continue
            seen.add(key)
            dedup_edges.append(e)

        return {"nodes": nodes, "edges": dedup_edges}

    @staticmethod
    def _edge_key(a: str, b: str) -> Tuple[str, str]:
        aa, bb = (a, b) if a <= b else (b, a)
        return (aa, bb)