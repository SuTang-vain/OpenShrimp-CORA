#!/usr/bin/env python3
"""
RAG文档处理器实现
支持多种文档类型的处理和分块策略

运行环境: Python 3.11+
依赖: asyncio, typing, re, json
"""

import asyncio
import json
import re
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base import (
    BaseDocumentProcessor, Document, DocumentChunk, DocumentType, ChunkingStrategy,
    DocumentProcessingError
)


class TextDocumentProcessor(BaseDocumentProcessor):
    """文本文档处理器
    
    支持纯文本文档的处理和多种分块策略
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.chunk_size = config.get('chunk_size', 1000)
        self.chunk_overlap = config.get('chunk_overlap', 200)
        self.strategy = ChunkingStrategy(config.get('strategy', 'fixed_size'))
        self.min_chunk_size = config.get('min_chunk_size', 100)
        self.max_chunk_size = config.get('max_chunk_size', 2000)
        self.dynamic_chunking = bool(config.get('dynamic_chunking', False))
        self._profiles = {
            'code': {'chunk_size': 400, 'overlap': 100},
            'report': {'chunk_size': 1000, 'overlap': 120},
            'table': {'chunk_size': 180, 'overlap': 30},
        }
    
    def validate_config(self) -> bool:
        """验证配置"""
        if self.chunk_size <= 0 or self.chunk_overlap < 0:
            return False
        if self.chunk_overlap >= self.chunk_size:
            return False
        return True
    
    def get_supported_types(self) -> List[DocumentType]:
        """获取支持的文档类型"""
        return [DocumentType.TEXT, DocumentType.MARKDOWN]
    
    async def process_document(self, document: Document) -> List[DocumentChunk]:
        """处理文档，生成文档块"""
        try:
            if document.doc_type not in self.get_supported_types():
                raise DocumentProcessingError(f"不支持的文档类型: {document.doc_type}")
            
            # 动态调整分块参数（可选）
            if self.dynamic_chunking:
                doc_profile = self._infer_profile(document)
                prof = self._profiles.get(doc_profile)
                if prof:
                    self.chunk_size = max(self.min_chunk_size, min(prof['chunk_size'], self.max_chunk_size))
                    self.chunk_overlap = prof['overlap']
            # 预处理文本
            processed_text = self._preprocess_text(document.content)
            
            # 根据策略分块
            if self.strategy == ChunkingStrategy.FIXED_SIZE:
                chunks = await self._chunk_by_fixed_size(processed_text, document)
            elif self.strategy == ChunkingStrategy.SENTENCE:
                chunks = await self._chunk_by_sentence(processed_text, document)
            elif self.strategy == ChunkingStrategy.PARAGRAPH:
                chunks = await self._chunk_by_paragraph(processed_text, document)
            elif self.strategy == ChunkingStrategy.SEMANTIC:
                chunks = await self._chunk_by_semantic(processed_text, document)
            elif self.strategy == ChunkingStrategy.RECURSIVE:
                chunks = await self._chunk_recursively(processed_text, document)
            else:
                chunks = await self._chunk_by_fixed_size(processed_text, document)
            
            return chunks
            
        except Exception as e:
            raise DocumentProcessingError(f"文档处理失败: {str(e)}") from e

    def _infer_profile(self, document: Document) -> str:
        """基于文档类型与元数据推断分块配置档位"""
        # 明确标注
        t = document.metadata.get('content_type') or document.metadata.get('doc_category')
        if t in self._profiles:
            return t
        # 按类型猜测
        if document.doc_type in (DocumentType.JSON, DocumentType.CSV):
            return 'table'
        title = (document.title or '').lower()
        if any(k in title for k in ['report', 'paper', '白皮书', '报告']):
            return 'report'
        # 代码/技术类关键词
        text = document.content[:2000].lower()
        if any(k in text for k in ['def ', 'class ', '{', '}', 'function', '#include']):
            return 'code'
        # 默认报告型
        return 'report'

    def _preprocess_text(self, text: str) -> str:
        """预处理文本：规范空白与可选移除特殊字符"""
        text = re.sub(r'\s+', ' ', text)
        if self.config.get('remove_special_chars', False):
            text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
        return text.strip()

    async def _chunk_by_fixed_size(self, text: str, document: Document) -> List[DocumentChunk]:
        """固定大小分块"""
        chunks: List[DocumentChunk] = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + self.chunk_size

            # 如果不是最后一块，尝试在单词边界分割
            if end < len(text):
                space_pos = text.rfind(' ', start, end)
                if space_pos > start:
                    end = space_pos

            chunk_content = text[start:end].strip()

            if len(chunk_content) >= self.min_chunk_size:
                chunk = DocumentChunk(
                    content=chunk_content,
                    chunk_id=f"{document.doc_id}_chunk_{chunk_index}",
                    doc_id=document.doc_id,
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end,
                    metadata={
                        'strategy': self.strategy.value,
                        'original_length': len(text),
                        'chunk_length': len(chunk_content),
                        **document.metadata
                    },
                    overlap_with_prev=self.chunk_overlap if chunk_index > 0 else 0
                )
                chunks.append(chunk)
                chunk_index += 1

            # 计算下一个块的起始位置（考虑重叠）
            start = max(start + 1, end - self.chunk_overlap)

        return chunks

    async def _chunk_by_sentence(self, text: str, document: Document) -> List[DocumentChunk]:
        """按句子分块"""
        sentences = re.split(r'[.!?。！？]', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks: List[DocumentChunk] = []
        current_chunk = ""
        chunk_index = 0
        start_char = 0

        for sentence in sentences:
            potential_chunk = current_chunk + sentence + "。"

            if len(potential_chunk) > self.chunk_size and current_chunk:
                chunk = DocumentChunk(
                    content=current_chunk.strip(),
                    chunk_id=f"{document.doc_id}_chunk_{chunk_index}",
                    doc_id=document.doc_id,
                    chunk_index=chunk_index,
                    start_char=start_char,
                    end_char=start_char + len(current_chunk),
                    metadata={
                        'strategy': self.strategy.value,
                        'sentence_count': current_chunk.count('。') + current_chunk.count('.'),
                        **document.metadata
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
                start_char += len(current_chunk)
                current_chunk = sentence + "。"
            else:
                current_chunk = potential_chunk

        if current_chunk.strip():
            chunk = DocumentChunk(
                content=current_chunk.strip(),
                chunk_id=f"{document.doc_id}_chunk_{chunk_index}",
                doc_id=document.doc_id,
                chunk_index=chunk_index,
                start_char=start_char,
                end_char=start_char + len(current_chunk),
                metadata={
                    'strategy': self.strategy.value,
                    'sentence_count': current_chunk.count('。') + current_chunk.count('.'),
                    **document.metadata
                }
            )
            chunks.append(chunk)

        return chunks

    async def _chunk_by_paragraph(self, text: str, document: Document) -> List[DocumentChunk]:
        """按段落分块"""
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks: List[DocumentChunk] = []
        current_chunk = ""
        chunk_index = 0
        start_char = 0

        for paragraph in paragraphs:
            potential_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph

            if len(potential_chunk) > self.chunk_size and current_chunk:
                chunk = DocumentChunk(
                    content=current_chunk.strip(),
                    chunk_id=f"{document.doc_id}_chunk_{chunk_index}",
                    doc_id=document.doc_id,
                    chunk_index=chunk_index,
                    start_char=start_char,
                    end_char=start_char + len(current_chunk),
                    metadata={
                        'strategy': self.strategy.value,
                        'paragraph_count': current_chunk.count('\n\n') + 1,
                        **document.metadata
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
                start_char += len(current_chunk)
                current_chunk = paragraph
            else:
                current_chunk = potential_chunk

        if current_chunk.strip():
            chunk = DocumentChunk(
                content=current_chunk.strip(),
                chunk_id=f"{document.doc_id}_chunk_{chunk_index}",
                doc_id=document.doc_id,
                chunk_index=chunk_index,
                start_char=start_char,
                end_char=start_char + len(current_chunk),
                metadata={
                    'strategy': self.strategy.value,
                    'paragraph_count': current_chunk.count('\n\n') + 1,
                    **document.metadata
                }
            )
            chunks.append(chunk)

        return chunks

    async def _chunk_by_semantic(self, text: str, document: Document) -> List[DocumentChunk]:
        """语义分块（简化实现）"""
        paragraphs = text.split('\n\n')
        semantic_chunks: List[str] = []

        for paragraph in paragraphs:
            if len(paragraph.strip()) < self.min_chunk_size:
                continue
            if len(paragraph) > self.chunk_size:
                sentences = re.split(r'[.!?。！？]', paragraph)
                current_chunk = ""
                for sentence in sentences:
                    if not sentence.strip():
                        continue
                    potential_chunk = current_chunk + sentence + "。"
                    if len(potential_chunk) > self.chunk_size and current_chunk:
                        semantic_chunks.append(current_chunk.strip())
                        current_chunk = sentence + "。"
                    else:
                        current_chunk = potential_chunk
                if current_chunk.strip():
                    semantic_chunks.append(current_chunk.strip())
            else:
                semantic_chunks.append(paragraph.strip())

        chunks: List[DocumentChunk] = []
        start_char = 0
        for i, chunk_content in enumerate(semantic_chunks):
            chunk = DocumentChunk(
                content=chunk_content,
                chunk_id=f"{document.doc_id}_chunk_{i}",
                doc_id=document.doc_id,
                chunk_index=i,
                start_char=start_char,
                end_char=start_char + len(chunk_content),
                metadata={
                    'strategy': self.strategy.value,
                    'semantic_score': 0.8,
                    **document.metadata
                }
            )
            chunks.append(chunk)
            start_char += len(chunk_content)

        return chunks

    async def _chunk_recursively(self, text: str, document: Document) -> List[DocumentChunk]:
        """递归分块"""
        def recursive_split(text: str, separators: List[str], current_size: int) -> List[str]:
            if len(text) <= current_size:
                return [text] if text.strip() else []
            if not separators:
                return [text[i:i+current_size] for i in range(0, len(text), current_size)]
            separator = separators[0]
            remaining_separators = separators[1:]
            parts = text.split(separator)
            result: List[str] = []
            current_chunk = ""
            for part in parts:
                potential_chunk = current_chunk + separator + part if current_chunk else part
                if len(potential_chunk) <= current_size:
                    current_chunk = potential_chunk
                else:
                    if current_chunk:
                        result.extend(recursive_split(current_chunk, remaining_separators, current_size))
                    current_chunk = part
            if current_chunk:
                result.extend(recursive_split(current_chunk, remaining_separators, current_size))
            return result

        separators = ['\n\n', '\n', '. ', '。', ' ']
        text_chunks = recursive_split(text, separators, self.chunk_size)

        chunks: List[DocumentChunk] = []
        start_char = 0
        for i, chunk_content in enumerate(text_chunks):
            if len(chunk_content.strip()) < self.min_chunk_size:
                continue
            chunk = DocumentChunk(
                content=chunk_content.strip(),
                chunk_id=f"{document.doc_id}_chunk_{i}",
                doc_id=document.doc_id,
                chunk_index=i,
                start_char=start_char,
                end_char=start_char + len(chunk_content),
                metadata={
                    'strategy': self.strategy.value,
                    'recursion_level': len(separators),
                    **document.metadata
                }
            )
            chunks.append(chunk)
            start_char += len(chunk_content)

        return chunks


class EnhancedDocumentProcessor(BaseDocumentProcessor):
    """增强型文档处理器

    在现有Text/JSON处理器基础上，提供策略自适应与类型路由。
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.text = TextDocumentProcessor({
            **config,
            'dynamic_chunking': True
        })
        self.json = JSONDocumentProcessor(config)

    def validate_config(self) -> bool:
        return self.text.validate_config() and self.json.validate_config()

    def get_supported_types(self) -> List[DocumentType]:
        return [DocumentType.TEXT, DocumentType.MARKDOWN, DocumentType.JSON]

    async def process_document(self, document: Document) -> List[DocumentChunk]:
        try:
            if document.doc_type in (DocumentType.JSON,):
                return await self.json.process_document(document)
            else:
                return await self.text.process_document(document)
        except Exception as e:
            raise DocumentProcessingError(f"增强型文档处理失败: {str(e)}") from e
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 清理多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符（可选）
        if self.config.get('remove_special_chars', False):
            text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
        return text.strip()
    
    async def _chunk_by_fixed_size(self, text: str, document: Document) -> List[DocumentChunk]:
        """固定大小分块"""
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # 如果不是最后一块，尝试在单词边界分割
            if end < len(text):
                # 向后查找空格
                space_pos = text.rfind(' ', start, end)
                if space_pos > start:
                    end = space_pos
            
            chunk_content = text[start:end].strip()
            
            if len(chunk_content) >= self.min_chunk_size:
                chunk = DocumentChunk(
                    content=chunk_content,
                    chunk_id=f"{document.doc_id}_chunk_{chunk_index}",
                    doc_id=document.doc_id,
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end,
                    metadata={
                        'strategy': self.strategy.value,
                        'original_length': len(text),
                        'chunk_length': len(chunk_content),
                        **document.metadata
                    },
                    overlap_with_prev=self.chunk_overlap if chunk_index > 0 else 0
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # 计算下一个块的起始位置（考虑重叠）
            start = max(start + 1, end - self.chunk_overlap)
        
        return chunks
    
    async def _chunk_by_sentence(self, text: str, document: Document) -> List[DocumentChunk]:
        """按句子分块"""
        # 简单的句子分割（可以使用更复杂的NLP库）
        sentences = re.split(r'[.!?。！？]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        start_char = 0
        
        for sentence in sentences:
            # 检查添加这个句子是否会超过大小限制
            potential_chunk = current_chunk + sentence + "。"
            
            if len(potential_chunk) > self.chunk_size and current_chunk:
                # 创建当前块
                chunk = DocumentChunk(
                    content=current_chunk.strip(),
                    chunk_id=f"{document.doc_id}_chunk_{chunk_index}",
                    doc_id=document.doc_id,
                    chunk_index=chunk_index,
                    start_char=start_char,
                    end_char=start_char + len(current_chunk),
                    metadata={
                        'strategy': self.strategy.value,
                        'sentence_count': current_chunk.count('。') + current_chunk.count('.'),
                        **document.metadata
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
                start_char += len(current_chunk)
                current_chunk = sentence + "。"
            else:
                current_chunk = potential_chunk
        
        # 处理最后一个块
        if current_chunk.strip():
            chunk = DocumentChunk(
                content=current_chunk.strip(),
                chunk_id=f"{document.doc_id}_chunk_{chunk_index}",
                doc_id=document.doc_id,
                chunk_index=chunk_index,
                start_char=start_char,
                end_char=start_char + len(current_chunk),
                metadata={
                    'strategy': self.strategy.value,
                    'sentence_count': current_chunk.count('。') + current_chunk.count('.'),
                    **document.metadata
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _chunk_by_paragraph(self, text: str, document: Document) -> List[DocumentChunk]:
        """按段落分块"""
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        start_char = 0
        
        for paragraph in paragraphs:
            potential_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            
            if len(potential_chunk) > self.chunk_size and current_chunk:
                # 创建当前块
                chunk = DocumentChunk(
                    content=current_chunk.strip(),
                    chunk_id=f"{document.doc_id}_chunk_{chunk_index}",
                    doc_id=document.doc_id,
                    chunk_index=chunk_index,
                    start_char=start_char,
                    end_char=start_char + len(current_chunk),
                    metadata={
                        'strategy': self.strategy.value,
                        'paragraph_count': current_chunk.count('\n\n') + 1,
                        **document.metadata
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
                start_char += len(current_chunk)
                current_chunk = paragraph
            else:
                current_chunk = potential_chunk
        
        # 处理最后一个块
        if current_chunk.strip():
            chunk = DocumentChunk(
                content=current_chunk.strip(),
                chunk_id=f"{document.doc_id}_chunk_{chunk_index}",
                doc_id=document.doc_id,
                chunk_index=chunk_index,
                start_char=start_char,
                end_char=start_char + len(current_chunk),
                metadata={
                    'strategy': self.strategy.value,
                    'paragraph_count': current_chunk.count('\n\n') + 1,
                    **document.metadata
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _chunk_by_semantic(self, text: str, document: Document) -> List[DocumentChunk]:
        """语义分块（简化实现）"""
        # 这里使用简化的语义分块，实际实现可能需要使用NLP模型
        # 当前实现基于句子和段落的组合
        
        # 首先按段落分割
        paragraphs = text.split('\n\n')
        semantic_chunks = []
        
        for paragraph in paragraphs:
            if len(paragraph.strip()) < self.min_chunk_size:
                continue
            
            # 如果段落太长，按句子进一步分割
            if len(paragraph) > self.chunk_size:
                sentences = re.split(r'[.!?。！？]', paragraph)
                current_chunk = ""
                
                for sentence in sentences:
                    if not sentence.strip():
                        continue
                    
                    potential_chunk = current_chunk + sentence + "。"
                    if len(potential_chunk) > self.chunk_size and current_chunk:
                        semantic_chunks.append(current_chunk.strip())
                        current_chunk = sentence + "。"
                    else:
                        current_chunk = potential_chunk
                
                if current_chunk.strip():
                    semantic_chunks.append(current_chunk.strip())
            else:
                semantic_chunks.append(paragraph.strip())
        
        # 转换为DocumentChunk对象
        chunks = []
        start_char = 0
        
        for i, chunk_content in enumerate(semantic_chunks):
            chunk = DocumentChunk(
                content=chunk_content,
                chunk_id=f"{document.doc_id}_chunk_{i}",
                doc_id=document.doc_id,
                chunk_index=i,
                start_char=start_char,
                end_char=start_char + len(chunk_content),
                metadata={
                    'strategy': self.strategy.value,
                    'semantic_score': 0.8,  # 模拟语义相关性分数
                    **document.metadata
                }
            )
            chunks.append(chunk)
            start_char += len(chunk_content)
        
        return chunks
    
    async def _chunk_recursively(self, text: str, document: Document) -> List[DocumentChunk]:
        """递归分块"""
        def recursive_split(text: str, separators: List[str], current_size: int) -> List[str]:
            """递归分割文本"""
            if len(text) <= current_size:
                return [text] if text.strip() else []
            
            if not separators:
                # 如果没有分隔符了，强制按字符分割
                return [text[i:i+current_size] for i in range(0, len(text), current_size)]
            
            separator = separators[0]
            remaining_separators = separators[1:]
            
            parts = text.split(separator)
            result = []
            current_chunk = ""
            
            for part in parts:
                potential_chunk = current_chunk + separator + part if current_chunk else part
                
                if len(potential_chunk) <= current_size:
                    current_chunk = potential_chunk
                else:
                    if current_chunk:
                        result.extend(recursive_split(current_chunk, remaining_separators, current_size))
                    current_chunk = part
            
            if current_chunk:
                result.extend(recursive_split(current_chunk, remaining_separators, current_size))
            
            return result
        
        # 定义分隔符优先级
        separators = ['\n\n', '\n', '. ', '。', ' ']
        
        # 执行递归分割
        text_chunks = recursive_split(text, separators, self.chunk_size)
        
        # 转换为DocumentChunk对象
        chunks = []
        start_char = 0
        
        for i, chunk_content in enumerate(text_chunks):
            if len(chunk_content.strip()) < self.min_chunk_size:
                continue
            
            chunk = DocumentChunk(
                content=chunk_content.strip(),
                chunk_id=f"{document.doc_id}_chunk_{i}",
                doc_id=document.doc_id,
                chunk_index=i,
                start_char=start_char,
                end_char=start_char + len(chunk_content),
                metadata={
                    'strategy': self.strategy.value,
                    'recursion_level': len(separators),
                    **document.metadata
                }
            )
            chunks.append(chunk)
            start_char += len(chunk_content)
        
        return chunks


class JSONDocumentProcessor(BaseDocumentProcessor):
    """JSON文档处理器
    
    专门处理JSON格式的文档
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.extract_fields = config.get('extract_fields', [])
        self.flatten_nested = config.get('flatten_nested', True)
        self.chunk_size = config.get('chunk_size', 1000)
    
    def validate_config(self) -> bool:
        """验证配置"""
        return self.chunk_size > 0
    
    def get_supported_types(self) -> List[DocumentType]:
        """获取支持的文档类型"""
        return [DocumentType.JSON]
    
    async def process_document(self, document: Document) -> List[DocumentChunk]:
        """处理JSON文档"""
        try:
            # 解析JSON
            json_data = json.loads(document.content)
            
            # 提取文本内容
            text_content = self._extract_text_from_json(json_data)
            
            # 分块
            chunks = await self._chunk_json_content(text_content, document, json_data)
            
            return chunks
            
        except json.JSONDecodeError as e:
            raise DocumentProcessingError(f"JSON解析失败: {str(e)}") from e
        except Exception as e:
            raise DocumentProcessingError(f"JSON文档处理失败: {str(e)}") from e
    
    def _extract_text_from_json(self, data: Any, path: str = "") -> List[tuple]:
        """从JSON中提取文本内容
        
        Returns:
            (path, value) 元组列表
        """
        text_items = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                
                # 如果指定了提取字段，只提取这些字段
                if self.extract_fields and key not in self.extract_fields:
                    continue
                
                if isinstance(value, (dict, list)):
                    if self.flatten_nested:
                        text_items.extend(self._extract_text_from_json(value, current_path))
                else:
                    text_items.append((current_path, str(value)))
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                if isinstance(item, (dict, list)):
                    if self.flatten_nested:
                        text_items.extend(self._extract_text_from_json(item, current_path))
                else:
                    text_items.append((current_path, str(item)))
        
        else:
            text_items.append((path, str(data)))
        
        return text_items
    
    async def _chunk_json_content(self, text_items: List[tuple], 
                                document: Document, 
                                original_data: Any) -> List[DocumentChunk]:
        """对JSON内容进行分块"""
        chunks = []
        current_chunk_items = []
        current_chunk_size = 0
        chunk_index = 0
        
        for path, value in text_items:
            item_text = f"{path}: {value}\n"
            item_size = len(item_text)
            
            if current_chunk_size + item_size > self.chunk_size and current_chunk_items:
                # 创建当前块
                chunk_content = "".join([f"{p}: {v}\n" for p, v in current_chunk_items])
                
                chunk = DocumentChunk(
                    content=chunk_content.strip(),
                    chunk_id=f"{document.doc_id}_chunk_{chunk_index}",
                    doc_id=document.doc_id,
                    chunk_index=chunk_index,
                    start_char=0,  # JSON中位置不太适用
                    end_char=len(chunk_content),
                    metadata={
                        'strategy': 'json_field_based',
                        'field_count': len(current_chunk_items),
                        'json_paths': [p for p, v in current_chunk_items],
                        **document.metadata
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # 重置当前块
                current_chunk_items = [(path, value)]
                current_chunk_size = item_size
            else:
                current_chunk_items.append((path, value))
                current_chunk_size += item_size
        
        # 处理最后一个块
        if current_chunk_items:
            chunk_content = "".join([f"{p}: {v}\n" for p, v in current_chunk_items])
            
            chunk = DocumentChunk(
                content=chunk_content.strip(),
                chunk_id=f"{document.doc_id}_chunk_{chunk_index}",
                doc_id=document.doc_id,
                chunk_index=chunk_index,
                start_char=0,
                end_char=len(chunk_content),
                metadata={
                    'strategy': 'json_field_based',
                    'field_count': len(current_chunk_items),
                    'json_paths': [p for p, v in current_chunk_items],
                    **document.metadata
                }
            )
            chunks.append(chunk)
        
        return chunks


class HTMLDocumentProcessor(BaseDocumentProcessor):
    """HTML文档处理器
    
    处理HTML文档，提取纯文本内容
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.remove_tags = config.get('remove_tags', ['script', 'style', 'nav', 'footer'])
        self.preserve_structure = config.get('preserve_structure', True)
        self.chunk_size = config.get('chunk_size', 1000)
    
    def validate_config(self) -> bool:
        """验证配置"""
        return self.chunk_size > 0
    
    def get_supported_types(self) -> List[DocumentType]:
        """获取支持的文档类型"""
        return [DocumentType.HTML]
    
    async def process_document(self, document: Document) -> List[DocumentChunk]:
        """处理HTML文档"""
        try:
            # 简化的HTML处理（实际应用中可能需要使用BeautifulSoup等库）
            text_content = self._extract_text_from_html(document.content)
            
            # 使用文本处理器进行分块
            text_processor = TextDocumentProcessor({
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.config.get('chunk_overlap', 200),
                'strategy': 'paragraph'
            })
            
            # 创建临时文本文档
            text_doc = Document(
                content=text_content,
                doc_id=document.doc_id,
                doc_type=DocumentType.TEXT,
                metadata={**document.metadata, 'original_type': 'html'}
            )
            
            chunks = await text_processor.process_document(text_doc)
            
            # 更新块的元数据
            for chunk in chunks:
                chunk.metadata.update({
                    'original_type': 'html',
                    'html_processed': True
                })
            
            return chunks
            
        except Exception as e:
            raise DocumentProcessingError(f"HTML文档处理失败: {str(e)}") from e
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """从HTML中提取文本内容"""
        # 简化的HTML标签移除（实际应用中建议使用专业的HTML解析库）
        
        # 移除指定的标签及其内容
        for tag in self.remove_tags:
            pattern = f'<{tag}[^>]*>.*?</{tag}>'
            html_content = re.sub(pattern, '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # 移除所有HTML标签
        text = re.sub(r'<[^>]+>', '', html_content)
        
        # 解码HTML实体
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&apos;': "'",
            '&nbsp;': ' '
        }
        
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        
        # 清理空白字符
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()