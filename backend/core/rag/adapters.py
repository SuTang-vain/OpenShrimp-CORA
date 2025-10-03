#!/usr/bin/env python3
"""
文档处理适配器
提供 IDocumentProcessor 抽象与基于文件路径的适配器，
以统一不同文档处理实现的接入方式。
"""

import pathlib
from abc import ABC, abstractmethod
from typing import List

from .base import Document, DocumentChunk, DocumentType, BaseDocumentProcessor


class IDocumentProcessor(ABC):
    """统一文档处理接口（面向文件路径）"""
    @abstractmethod
    def supports(self, file_ext: str) -> bool:
        pass

    @abstractmethod
    async def process(self, file_path: str) -> List[DocumentChunk]:
        pass


class FilePathProcessorAdapter(IDocumentProcessor):
    """将 BaseDocumentProcessor 适配为支持文件路径的接口"""
    def __init__(self, processor: BaseDocumentProcessor, default_type: DocumentType = DocumentType.TEXT):
        self.processor = processor
        self.default_type = default_type

    def supports(self, file_ext: str) -> bool:
        try:
            supported = self.processor.get_supported_types()
            # 简单映射: 依据扩展名猜测类型
            ext = (file_ext or '').lower().strip('.')
            mapping = {
                'txt': DocumentType.TEXT,
                'md': DocumentType.MARKDOWN,
                'json': DocumentType.JSON,
                'html': DocumentType.HTML,
                'htm': DocumentType.HTML,
            }
            return mapping.get(ext, self.default_type) in supported
        except Exception:
            return False

    async def process(self, file_path: str) -> List[DocumentChunk]:
        p = pathlib.Path(file_path)
        ext = p.suffix.lower().strip('.')
        mapping = {
            'txt': DocumentType.TEXT,
            'md': DocumentType.MARKDOWN,
            'json': DocumentType.JSON,
            'html': DocumentType.HTML,
            'htm': DocumentType.HTML,
        }
        doc_type = mapping.get(ext, self.default_type)
        content = p.read_text(encoding='utf-8', errors='ignore')
        document = Document(content=content, doc_type=doc_type, metadata={'source': str(p)})
        return await self.processor.process_document(document)