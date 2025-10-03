#!/usr/bin/env python3
"""
RAG向量存储实现
支持多种向量数据库的统一接口

运行环境: Python 3.11+
依赖: asyncio, typing, json, sqlite3
"""

import asyncio
import json
import sqlite3
import time
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import tempfile

from .base import (
    BaseVectorStore, VectorStoreType, DocumentChunk, RetrievalResult,
    VectorStoreError
)


class FAISSVectorStore(BaseVectorStore):
    """FAISS向量存储
    
    基于Facebook AI Similarity Search的向量存储实现
    """
    
    def __init__(self, store_type: VectorStoreType, config: Dict[str, Any]):
        super().__init__(store_type, config)
        self.index_path = config.get('index_path', 'faiss_index')
        self.metadata_path = config.get('metadata_path', 'faiss_metadata.db')
        self.index_type = config.get('index_type', 'flat')  # flat, ivf, hnsw
        
        # 模拟FAISS索引
        self.vectors: Dict[str, List[float]] = {}
        self.metadata_db = None
        self._initialize_storage()
    
    def _initialize_storage(self) -> None:
        """初始化存储"""
        # 创建SQLite数据库存储元数据
        self.metadata_db = sqlite3.connect(self.metadata_path, check_same_thread=False)
        cursor = self.metadata_db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                doc_id TEXT,
                content TEXT,
                chunk_index INTEGER,
                start_char INTEGER,
                end_char INTEGER,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.metadata_db.commit()
    
    def validate_config(self) -> bool:
        """验证配置"""
        return self.dimension > 0
    
    async def add_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """添加文档块"""
        try:
            cursor = self.metadata_db.cursor()
            
            for chunk in chunks:
                if not chunk.embedding:
                    raise VectorStoreError(f"文档块 {chunk.chunk_id} 缺少嵌入向量")
                
                # 存储向量
                self.vectors[chunk.chunk_id] = chunk.embedding
                
                # 存储元数据
                cursor.execute('''
                    INSERT OR REPLACE INTO chunks 
                    (chunk_id, doc_id, content, chunk_index, start_char, end_char, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    chunk.chunk_id,
                    chunk.doc_id,
                    chunk.content,
                    chunk.chunk_index,
                    chunk.start_char,
                    chunk.end_char,
                    json.dumps(chunk.metadata, ensure_ascii=False)
                ))
            
            self.metadata_db.commit()
            return True
            
        except Exception as e:
            raise VectorStoreError(f"添加文档块失败: {str(e)}") from e
    
    async def search(self, query_embedding: List[float], 
                    top_k: int = 5, 
                    filters: Optional[Dict[str, Any]] = None) -> List[RetrievalResult]:
        """向量搜索"""
        try:
            # 计算相似度
            similarities = []
            
            for chunk_id, vector in self.vectors.items():
                similarity = self._cosine_similarity(query_embedding, vector)
                similarities.append((chunk_id, similarity))
            
            # 排序并取top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_similarities = similarities[:top_k]
            
            # 获取文档块信息
            results = []
            cursor = self.metadata_db.cursor()
            
            for rank, (chunk_id, score) in enumerate(top_similarities):
                cursor.execute(
                    'SELECT * FROM chunks WHERE chunk_id = ?', 
                    (chunk_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    chunk = DocumentChunk(
                        content=row[2],
                        chunk_id=row[0],
                        doc_id=row[1],
                        chunk_index=row[3],
                        start_char=row[4],
                        end_char=row[5],
                        metadata=json.loads(row[6]) if row[6] else {},
                        embedding=self.vectors[chunk_id]
                    )
                    
                    # 应用过滤器
                    if filters and not self._apply_filters(chunk, filters):
                        continue
                    
                    result = RetrievalResult(
                        chunk=chunk,
                        score=score,
                        rank=rank,
                        retrieval_method='faiss_cosine'
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            raise VectorStoreError(f"向量搜索失败: {str(e)}") from e
    
    async def delete_chunks(self, chunk_ids: List[str]) -> bool:
        """删除文档块"""
        try:
            cursor = self.metadata_db.cursor()
            
            for chunk_id in chunk_ids:
                # 删除向量
                if chunk_id in self.vectors:
                    del self.vectors[chunk_id]
                
                # 删除元数据
                cursor.execute('DELETE FROM chunks WHERE chunk_id = ?', (chunk_id,))
            
            self.metadata_db.commit()
            return True
            
        except Exception as e:
            raise VectorStoreError(f"删除文档块失败: {str(e)}") from e
    
    async def update_chunk(self, chunk: DocumentChunk) -> bool:
        """更新文档块"""
        try:
            if not chunk.embedding:
                raise VectorStoreError(f"文档块 {chunk.chunk_id} 缺少嵌入向量")
            
            # 更新向量
            self.vectors[chunk.chunk_id] = chunk.embedding
            
            # 更新元数据
            cursor = self.metadata_db.cursor()
            cursor.execute('''
                UPDATE chunks SET 
                content = ?, metadata = ?
                WHERE chunk_id = ?
            ''', (
                chunk.content,
                json.dumps(chunk.metadata, ensure_ascii=False),
                chunk.chunk_id
            ))
            
            self.metadata_db.commit()
            return True
            
        except Exception as e:
            raise VectorStoreError(f"更新文档块失败: {str(e)}") from e
    
    async def get_chunk(self, chunk_id: str) -> Optional[DocumentChunk]:
        """获取文档块"""
        try:
            cursor = self.metadata_db.cursor()
            cursor.execute('SELECT * FROM chunks WHERE chunk_id = ?', (chunk_id,))
            row = cursor.fetchone()
            
            if row:
                return DocumentChunk(
                    content=row[2],
                    chunk_id=row[0],
                    doc_id=row[1],
                    chunk_index=row[3],
                    start_char=row[4],
                    end_char=row[5],
                    metadata=json.loads(row[6]) if row[6] else {},
                    embedding=self.vectors.get(chunk_id)
                )
            
            return None
            
        except Exception as e:
            raise VectorStoreError(f"获取文档块失败: {str(e)}") from e
    
    async def list_chunks(self, doc_id: Optional[str] = None, 
                         limit: int = 100, 
                         offset: int = 0) -> List[DocumentChunk]:
        """列出文档块"""
        try:
            cursor = self.metadata_db.cursor()
            
            if doc_id:
                cursor.execute(
                    'SELECT * FROM chunks WHERE doc_id = ? LIMIT ? OFFSET ?',
                    (doc_id, limit, offset)
                )
            else:
                cursor.execute(
                    'SELECT * FROM chunks LIMIT ? OFFSET ?',
                    (limit, offset)
                )
            
            rows = cursor.fetchall()
            chunks = []
            
            for row in rows:
                chunk = DocumentChunk(
                    content=row[2],
                    chunk_id=row[0],
                    doc_id=row[1],
                    chunk_index=row[3],
                    start_char=row[4],
                    end_char=row[5],
                    metadata=json.loads(row[6]) if row[6] else {},
                    embedding=self.vectors.get(row[0])
                )
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            raise VectorStoreError(f"列出文档块失败: {str(e)}") from e
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            cursor = self.metadata_db.cursor()
            cursor.execute('SELECT COUNT(*) FROM chunks')
            cursor.fetchone()
            return True
        except Exception:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            cursor = self.metadata_db.cursor()
            
            # 总块数
            cursor.execute('SELECT COUNT(*) FROM chunks')
            total_chunks = cursor.fetchone()[0]
            
            # 文档数
            cursor.execute('SELECT COUNT(DISTINCT doc_id) FROM chunks')
            total_docs = cursor.fetchone()[0]
            
            return {
                'total_chunks': total_chunks,
                'total_documents': total_docs,
                'vector_dimension': self.dimension,
                'index_type': self.index_type,
                'storage_path': self.index_path
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _apply_filters(self, chunk: DocumentChunk, filters: Dict[str, Any]) -> bool:
        """应用过滤器"""
        for key, value in filters.items():
            if key == 'doc_id':
                if chunk.doc_id != value:
                    return False
            elif key in chunk.metadata:
                if chunk.metadata[key] != value:
                    return False
        return True


class ChromaVectorStore(BaseVectorStore):
    """Chroma向量存储
    
    基于Chroma的向量存储实现
    """
    
    def __init__(self, store_type: VectorStoreType, config: Dict[str, Any]):
        super().__init__(store_type, config)
        self.collection_name = config.get('collection_name', 'default')
        self.persist_directory = config.get('persist_directory', './chroma_db')
        
        # 模拟Chroma存储
        self.collections: Dict[str, Dict[str, Any]] = {}
        self._initialize_collection()
    
    def _initialize_collection(self) -> None:
        """初始化集合"""
        if self.collection_name not in self.collections:
            self.collections[self.collection_name] = {
                'vectors': {},
                'metadata': {},
                'documents': {}
            }
    
    def validate_config(self) -> bool:
        """验证配置"""
        return bool(self.collection_name)
    
    async def add_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """添加文档块"""
        try:
            collection = self.collections[self.collection_name]
            
            for chunk in chunks:
                if not chunk.embedding:
                    raise VectorStoreError(f"文档块 {chunk.chunk_id} 缺少嵌入向量")
                
                collection['vectors'][chunk.chunk_id] = chunk.embedding
                collection['metadata'][chunk.chunk_id] = {
                    'doc_id': chunk.doc_id,
                    'chunk_index': chunk.chunk_index,
                    'start_char': chunk.start_char,
                    'end_char': chunk.end_char,
                    **chunk.metadata
                }
                collection['documents'][chunk.chunk_id] = chunk.content
            
            return True
            
        except Exception as e:
            raise VectorStoreError(f"添加文档块失败: {str(e)}") from e
    
    async def search(self, query_embedding: List[float], 
                    top_k: int = 5, 
                    filters: Optional[Dict[str, Any]] = None) -> List[RetrievalResult]:
        """向量搜索"""
        try:
            collection = self.collections[self.collection_name]
            similarities = []
            
            for chunk_id, vector in collection['vectors'].items():
                # 应用过滤器
                if filters:
                    metadata = collection['metadata'][chunk_id]
                    if not self._apply_filters_to_metadata(metadata, filters):
                        continue
                
                similarity = self._cosine_similarity(query_embedding, vector)
                similarities.append((chunk_id, similarity))
            
            # 排序并取top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_similarities = similarities[:top_k]
            
            # 构建结果
            results = []
            for rank, (chunk_id, score) in enumerate(top_similarities):
                metadata = collection['metadata'][chunk_id]
                content = collection['documents'][chunk_id]
                
                chunk = DocumentChunk(
                    content=content,
                    chunk_id=chunk_id,
                    doc_id=metadata['doc_id'],
                    chunk_index=metadata['chunk_index'],
                    start_char=metadata['start_char'],
                    end_char=metadata['end_char'],
                    metadata={k: v for k, v in metadata.items() 
                             if k not in ['doc_id', 'chunk_index', 'start_char', 'end_char']},
                    embedding=collection['vectors'][chunk_id]
                )
                
                result = RetrievalResult(
                    chunk=chunk,
                    score=score,
                    rank=rank,
                    retrieval_method='chroma_cosine'
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            raise VectorStoreError(f"向量搜索失败: {str(e)}") from e
    
    async def delete_chunks(self, chunk_ids: List[str]) -> bool:
        """删除文档块"""
        try:
            collection = self.collections[self.collection_name]
            
            for chunk_id in chunk_ids:
                collection['vectors'].pop(chunk_id, None)
                collection['metadata'].pop(chunk_id, None)
                collection['documents'].pop(chunk_id, None)
            
            return True
            
        except Exception as e:
            raise VectorStoreError(f"删除文档块失败: {str(e)}") from e
    
    async def update_chunk(self, chunk: DocumentChunk) -> bool:
        """更新文档块"""
        try:
            if not chunk.embedding:
                raise VectorStoreError(f"文档块 {chunk.chunk_id} 缺少嵌入向量")
            
            collection = self.collections[self.collection_name]
            
            collection['vectors'][chunk.chunk_id] = chunk.embedding
            collection['metadata'][chunk.chunk_id] = {
                'doc_id': chunk.doc_id,
                'chunk_index': chunk.chunk_index,
                'start_char': chunk.start_char,
                'end_char': chunk.end_char,
                **chunk.metadata
            }
            collection['documents'][chunk.chunk_id] = chunk.content
            
            return True
            
        except Exception as e:
            raise VectorStoreError(f"更新文档块失败: {str(e)}") from e
    
    async def get_chunk(self, chunk_id: str) -> Optional[DocumentChunk]:
        """获取文档块"""
        try:
            collection = self.collections[self.collection_name]
            
            if chunk_id not in collection['vectors']:
                return None
            
            metadata = collection['metadata'][chunk_id]
            content = collection['documents'][chunk_id]
            
            return DocumentChunk(
                content=content,
                chunk_id=chunk_id,
                doc_id=metadata['doc_id'],
                chunk_index=metadata['chunk_index'],
                start_char=metadata['start_char'],
                end_char=metadata['end_char'],
                metadata={k: v for k, v in metadata.items() 
                         if k not in ['doc_id', 'chunk_index', 'start_char', 'end_char']},
                embedding=collection['vectors'][chunk_id]
            )
            
        except Exception as e:
            raise VectorStoreError(f"获取文档块失败: {str(e)}") from e
    
    async def list_chunks(self, doc_id: Optional[str] = None, 
                         limit: int = 100, 
                         offset: int = 0) -> List[DocumentChunk]:
        """列出文档块"""
        try:
            collection = self.collections[self.collection_name]
            chunks = []
            
            chunk_ids = list(collection['vectors'].keys())
            
            # 过滤文档ID
            if doc_id:
                chunk_ids = [cid for cid in chunk_ids 
                           if collection['metadata'][cid]['doc_id'] == doc_id]
            
            # 分页
            chunk_ids = chunk_ids[offset:offset + limit]
            
            for chunk_id in chunk_ids:
                metadata = collection['metadata'][chunk_id]
                content = collection['documents'][chunk_id]
                
                chunk = DocumentChunk(
                    content=content,
                    chunk_id=chunk_id,
                    doc_id=metadata['doc_id'],
                    chunk_index=metadata['chunk_index'],
                    start_char=metadata['start_char'],
                    end_char=metadata['end_char'],
                    metadata={k: v for k, v in metadata.items() 
                             if k not in ['doc_id', 'chunk_index', 'start_char', 'end_char']},
                    embedding=collection['vectors'][chunk_id]
                )
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            raise VectorStoreError(f"列出文档块失败: {str(e)}") from e
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            return self.collection_name in self.collections
        except Exception:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            collection = self.collections[self.collection_name]
            
            total_chunks = len(collection['vectors'])
            doc_ids = set(metadata['doc_id'] for metadata in collection['metadata'].values())
            total_docs = len(doc_ids)
            
            return {
                'total_chunks': total_chunks,
                'total_documents': total_docs,
                'vector_dimension': self.dimension,
                'collection_name': self.collection_name,
                'persist_directory': self.persist_directory
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _apply_filters_to_metadata(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """应用过滤器到元数据"""
        for key, value in filters.items():
            if key in metadata and metadata[key] != value:
                return False
        return True


class InMemoryVectorStore(BaseVectorStore):
    """内存向量存储
    
    简单的内存向量存储实现，适用于开发和测试
    """
    
    def __init__(self, store_type: VectorStoreType, config: Dict[str, Any]):
        super().__init__(store_type, config)
        self.chunks: Dict[str, DocumentChunk] = {}
    
    def validate_config(self) -> bool:
        """验证配置"""
        return True
    
    async def add_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """添加文档块"""
        try:
            for chunk in chunks:
                self.chunks[chunk.chunk_id] = chunk
            return True
        except Exception as e:
            raise VectorStoreError(f"添加文档块失败: {str(e)}") from e
    
    async def search(self, query_embedding: List[float], 
                    top_k: int = 5, 
                    filters: Optional[Dict[str, Any]] = None) -> List[RetrievalResult]:
        """向量搜索"""
        try:
            similarities = []
            
            for chunk in self.chunks.values():
                if not chunk.embedding:
                    continue
                
                # 应用过滤器
                if filters and not self._apply_filters(chunk, filters):
                    continue
                
                similarity = self._cosine_similarity(query_embedding, chunk.embedding)
                similarities.append((chunk, similarity))
            
            # 排序并取top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_similarities = similarities[:top_k]
            
            # 构建结果
            results = []
            for rank, (chunk, score) in enumerate(top_similarities):
                result = RetrievalResult(
                    chunk=chunk,
                    score=score,
                    rank=rank,
                    retrieval_method='memory_cosine'
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            raise VectorStoreError(f"向量搜索失败: {str(e)}") from e
    
    async def delete_chunks(self, chunk_ids: List[str]) -> bool:
        """删除文档块"""
        try:
            for chunk_id in chunk_ids:
                self.chunks.pop(chunk_id, None)
            return True
        except Exception as e:
            raise VectorStoreError(f"删除文档块失败: {str(e)}") from e
    
    async def update_chunk(self, chunk: DocumentChunk) -> bool:
        """更新文档块"""
        try:
            self.chunks[chunk.chunk_id] = chunk
            return True
        except Exception as e:
            raise VectorStoreError(f"更新文档块失败: {str(e)}") from e
    
    async def get_chunk(self, chunk_id: str) -> Optional[DocumentChunk]:
        """获取文档块"""
        return self.chunks.get(chunk_id)
    
    async def list_chunks(self, doc_id: Optional[str] = None, 
                         limit: int = 100, 
                         offset: int = 0) -> List[DocumentChunk]:
        """列出文档块"""
        chunks = list(self.chunks.values())
        
        # 过滤文档ID
        if doc_id:
            chunks = [chunk for chunk in chunks if chunk.doc_id == doc_id]
        
        # 分页
        return chunks[offset:offset + limit]
    
    async def health_check(self) -> bool:
        """健康检查"""
        return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        doc_ids = set(chunk.doc_id for chunk in self.chunks.values())
        
        return {
            'total_chunks': len(self.chunks),
            'total_documents': len(doc_ids),
            'vector_dimension': self.dimension,
            'storage_type': 'memory'
        }
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _apply_filters(self, chunk: DocumentChunk, filters: Dict[str, Any]) -> bool:
        """应用过滤器"""
        for key, value in filters.items():
            if key == 'doc_id':
                if chunk.doc_id != value:
                    return False
            elif key in chunk.metadata:
                if chunk.metadata[key] != value:
                    return False
        return True