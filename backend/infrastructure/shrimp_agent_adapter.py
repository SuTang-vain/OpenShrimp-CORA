#!/usr/bin/env python3
"""
Shrimp_Agent 适配层
复用老项目的增强文档管理器（EnhancedDocumentManager）以提升v2的文档处理能力。

用途：
- 作为兼容桥接，调用老项目的文档预处理、缓存索引与多模态提取能力
- 将结果转换为 v2 RAG 引擎可消费的块结构（轻量字典格式），由 v2 再做嵌入与入库

运行环境：Python 3.11+
依赖：老项目 Shrimp_Agent 的增强文档管理器及其依赖库（PyMuPDF, python-docx, pandas, etc.）

注意：
- 该适配层仅做“预处理/分块与索引”的复用，不替换 v2 的嵌入与向量存储流程
- 为避免硬编码路径，自动定位工作目录并注入 Shrimp_Agent 到 sys.path
"""

import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ShrimpAgentAdapter:
    """Shrimp_Agent 文档管理器适配器

    - 动态注入老项目路径，导入 `EnhancedDocumentManager`
    - 统一转换老项目的块结构到 v2 可消费的轻量字典
    """

    def __init__(self, cache_dir: Optional[str] = None) -> None:
        self._enabled = False
        self._manager = None

        try:
            # 解析项目根路径：.../Shrimp_Search
            # 当前文件位于 .../shrimp-agent-v2/backend/infrastructure
            project_root = Path(__file__).resolve().parents[2]
            shrimp_agent_path = project_root / "Shrimp_Search" / "Shrimp_Agent"

            # 注入老项目路径
            sys.path.insert(0, str(shrimp_agent_path))

            # 导入老项目模块
            from enhanced_document_manager import EnhancedDocumentManager  # type: ignore

            # 默认复用工作区根目录下的 document_cache
            default_cache = project_root / "document_cache"
            cache_dir_path = Path(cache_dir).resolve() if cache_dir else default_cache

            # 初始化管理器
            self._manager = EnhancedDocumentManager(
                cache_dir=str(cache_dir_path),
                enable_cache=True,
                max_cache_size_mb=1000,
            )
            self._enabled = True
        except Exception as e:
            # 不抛出异常，降级为不可用；上层可检测 enabled 决定是否使用
            self._enabled = False
            self._manager = None
            print(f"[ShrimpAgentAdapter] 初始化失败，保持禁用: {e}")

    @property
    def enabled(self) -> bool:
        """适配器是否可用"""
        return self._enabled and self._manager is not None

    def process_document(self, file_path: str, force_reprocess: bool = False) -> List[Dict[str, Any]]:
        """调用老项目文档管理器处理文档并返回块列表（轻量字典）

        参数：
            file_path: 文档路径
            force_reprocess: 是否强制重新处理

        返回：
            List[Dict]：每个块包含 content, chunk_id, metadata 字段
        """
        if not self.enabled:
            return []

        try:
            # 获取文档块列表（老项目的 DocumentChunk 数据类）
            chunks = self._manager.process_document(file_path, force_reprocess=force_reprocess)
            return [self._to_v2_chunk_dict(c) for c in chunks]
        except Exception as e:
            print(f"[ShrimpAgentAdapter] 处理文档失败: {e}")
            return []

    def list_documents(self) -> List[Dict[str, Any]]:
        """列出已缓存文档（转换为通用字典）"""
        if not self.enabled:
            return []

        try:
            docs = self._manager.list_documents()
            return [self._normalize_doc_info(d) for d in docs]
        except Exception as e:
            print(f"[ShrimpAgentAdapter] 列出文档失败: {e}")
            return []

    def get_document_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """根据文件路径获取文档信息"""
        if not self.enabled:
            return None
        try:
            meta = self._manager.get_document_info(file_path)
            return self._normalize_doc_meta(meta) if meta else None
        except Exception as e:
            print(f"[ShrimpAgentAdapter] 获取文档信息失败: {e}")
            return None

    # -------------------------
    # 内部工具：结构转换
    # -------------------------
    def _to_v2_chunk_dict(self, chunk_obj: Any) -> Dict[str, Any]:
        """将老项目的 DocumentChunk 转为 v2 轻量字典结构

        字段约定：
            - chunk_id: 唯一ID
            - content: 文本内容
            - metadata: 附加信息（页码/类型/来源等）
            - embedding: 留空，由 v2 执行嵌入
        """
        try:
            return {
                "chunk_id": getattr(chunk_obj, "chunk_id", None),
                "content": getattr(chunk_obj, "content", ""),
                "metadata": getattr(chunk_obj, "metadata", {}) or {},
                "embedding": None,
            }
        except Exception:
            # 宽松降级：尝试按字典处理
            if isinstance(chunk_obj, dict):
                return {
                    "chunk_id": chunk_obj.get("chunk_id"),
                    "content": chunk_obj.get("content", ""),
                    "metadata": chunk_obj.get("metadata", {}) or {},
                    "embedding": None,
                }
            return {
                "chunk_id": None,
                "content": str(chunk_obj),
                "metadata": {},
                "embedding": None,
            }

    def _normalize_doc_info(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """统一文档列表项结构"""
        return {
            "id": doc.get("id") or doc.get("file_path"),
            "filename": doc.get("filename"),
            "title": doc.get("title"),
            "size": doc.get("size"),
            "type": doc.get("type"),
            "uploaded_at": doc.get("uploaded_at"),
            "processed": doc.get("processed", True),
            "chunk_count": doc.get("chunk_count", 0),
            "content_type": doc.get("content_type", "unknown"),
        }

    def _normalize_doc_meta(self, meta_obj: Any) -> Optional[Dict[str, Any]]:
        """规范化文档元数据对象为字典"""
        try:
            # dataclass -> dict
            from dataclasses import asdict
            return asdict(meta_obj)
        except Exception:
            if isinstance(meta_obj, dict):
                return meta_obj
        return None


# 便捷函数
_adapter_instance: Optional[ShrimpAgentAdapter] = None


def get_shrimp_adapter(cache_dir: Optional[str] = None) -> ShrimpAgentAdapter:
    """获取（单例）适配器实例"""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = ShrimpAgentAdapter(cache_dir=cache_dir)
    return _adapter_instance