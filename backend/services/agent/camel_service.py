#!/usr/bin/env python3
"""
CAMEL 智能体服务（shrimp-agent-v2）
封装 Coordinator / Searcher 等 CAMEL 代理，提供搜索入口并可选将结果入库到 RAG。
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional

from backend.core.agents.camel_base import CAMELTask, TaskType
from backend.core.agents.camel_agents import CoordinatorAgent, SearcherAgent
from backend.core.rag import Document, DocumentType


class CamelAgentService:
    """CAMEL 多智能体服务封装"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}
        llm_interface = self.config.get('llm_manager')

        # 初始化核心代理
        self.coordinator = CoordinatorAgent(
            agent_id=self.config.get('available_agents', {}).get('coordinator', 'coordinator_001'),
            config={
                'available_agents': self.config.get('available_agents', {}),
                'max_subtasks': 5,
                'llm_interface': llm_interface,
            }
        )

        self.searcher = SearcherAgent(
            agent_id=self.config.get('available_agents', {}).get('searcher', 'searcher_001'),
            config={
                'search_engines': self.config.get('search_engines', ['google', 'bing']),
                'max_results': self.config.get('max_results', 10),
                'llm_interface': llm_interface,
            }
        )

        # 可选 RAG 引擎，用于入库
        self.rag_engine = self.config.get('rag_engine')

    async def search(self, query: str, *, search_type: str = 'web', max_results: Optional[int] = None,
                     ingest_to_rag: bool = True) -> Dict[str, Any]:
        """执行 CAMEL 搜索

        Args:
            query: 搜索查询
            search_type: 'web' 或 'document'
            max_results: 最大返回数量（可选，覆盖默认）
            ingest_to_rag: 是否将结果入库到 RAG

        Returns:
            字典结果，包含搜索结果与元数据
        """
        task = CAMELTask(
            task_id=str(uuid.uuid4()),
            task_type=TaskType.SEARCH,
            description=query,
            input_data={
                'query': query,
                'search_type': search_type,
                'max_results': max_results or self.config.get('max_results', 10)
            }
        )

        camel_result = await self.searcher.process_task(task)

        # 成功则尝试入库到 RAG
        if camel_result.success and ingest_to_rag and self.rag_engine:
            await self._ingest_search_results_to_rag(
                query,
                camel_result.result_data.get('results', [])
            )

        return {
            'success': camel_result.success,
            'query': query,
            'results': camel_result.result_data.get('results', []),
            'total_found': camel_result.result_data.get('total_found', 0),
            'metadata': camel_result.metadata,
            'execution_time': camel_result.execution_time,
            'quality_score': camel_result.quality_score,
            'error': camel_result.error_message,
        }

    async def _ingest_search_results_to_rag(self, query: str, results: List[Dict[str, Any]]) -> None:
        """将搜索结果入库到 RAG 引擎"""
        try:
            tasks = []
            for idx, item in enumerate(results):
                content = item.get('content') or item.get('snippet') or ''
                if not content:
                    continue

                doc = Document(
                    content=content,
                    metadata={
                        'source': item.get('source'),
                        'url': item.get('url'),
                        'relevance_score': item.get('relevance_score'),
                        'ingest_query': query,
                        'title': item.get('title'),
                        'rank_index': idx,
                    },
                    title=item.get('title'),
                    source=item.get('url'),
                    doc_type=DocumentType.HTML if item.get('url') else DocumentType.TEXT,
                    tags=['camel_search']
                )
                tasks.append(self.rag_engine.add_document(doc))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        except Exception:
            # 入库失败不阻断主流程
            pass