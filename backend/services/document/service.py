#!/usr/bin/env python3
"""
文档服务
提供文档管理、处理和存储功能

运行环境: Python 3.11+
依赖: asyncio, typing, pathlib
"""

import asyncio
import os
import json
import hashlib
from typing import Dict, Any, List, Optional, Union, BinaryIO
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from backend.core.rag import RAGEngine, DocumentType, ChunkingStrategy, RAGError
from backend.core.rag.base import Document, DocumentChunk
from backend.api.schemas.document import DocumentInfo, DocumentStatus, ProcessingResult
from backend.shared.utils.retry import retry_async
from backend.infrastructure.shrimp_agent_adapter import get_shrimp_adapter


class DocumentService:
    """文档服务
    
    管理文档的上传、处理、存储和检索
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rag_engine = config.get('rag_engine')
        self.storage_path = Path(config.get('storage_path', './data/documents'))
        self.max_file_size = config.get('max_file_size', 50 * 1024 * 1024)  # 50MB
        self.supported_formats = config.get('supported_formats', [
            '.txt', '.md', '.pdf', '.docx', '.html', '.json', '.csv'
        ])
        self.enable_ocr = config.get('enable_ocr', False)
        self.enable_auto_processing = config.get('enable_auto_processing', True)
        self.enable_adapter = config.get('enable_adapter', True)
        self.adapter = get_shrimp_adapter() if self.enable_adapter else None
        
        # 确保存储目录存在
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 文档元数据存储（简化实现，生产环境应使用数据库）
        self.document_metadata: Dict[str, Dict[str, Any]] = {}
        self.processing_queue: List[str] = []
        self.processing_status: Dict[str, str] = {}
        
        # 统计信息
        self.stats = {
            'total_documents': 0,
            'total_chunks': 0,
            'total_size': 0,
            'processing_success': 0,
            'processing_failed': 0,
            'format_distribution': defaultdict(int),
            'processing_time': defaultdict(float)
        }
        
        # 加载现有文档元数据
        self._load_metadata()
    
    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        auto_process: bool = True
    ) -> str:
        """上传文档
        
        Args:
            file_content: 文件内容
            filename: 文件名
            content_type: 内容类型
            metadata: 文档元数据
            user_id: 用户ID
            auto_process: 是否自动处理
            
        Returns:
            文档ID
        """
        # 验证文件
        await self._validate_file(file_content, filename, content_type)
        
        # 计算内容哈希并进行重复检测
        content_hash = self._compute_content_hash(file_content)
        existing_doc_id = None
        for did, meta in self.document_metadata.items():
            if meta.get('content_hash') == content_hash:
                existing_doc_id = did
                break

        if existing_doc_id:
            # 内容完全重复，拒绝重复上传
            raise ValueError(f"文档内容重复，已存在: {existing_doc_id}")

        # 生成文档ID（保持兼容的时间戳+内容哈希前缀）
        doc_id = self._generate_document_id(filename, file_content)
        
        # 保存文件
        file_path = await self._save_file(doc_id, filename, file_content)
        
        # 创建文档元数据
        doc_metadata = {
            'doc_id': doc_id,
            'filename': filename,
            'original_filename': filename,
            'content_type': content_type,
            'file_path': str(file_path),
            'file_size': len(file_content),
            'upload_time': datetime.now().isoformat(),
            'user_id': user_id,
            'status': DocumentStatus.UPLOADED.value,
            'processing_attempts': 0,
            'chunks_count': 0,
            'content_hash': content_hash,
            'metadata': metadata or {},
            'tags': metadata.get('tags', []) if metadata else [],
            'language': metadata.get('language', 'auto') if metadata else 'auto'
        }
        
        # 存储元数据
        self.document_metadata[doc_id] = doc_metadata
        await self._save_metadata()
        
        # 更新统计信息
        self.stats['total_documents'] += 1
        self.stats['total_size'] += len(file_content)
        file_ext = Path(filename).suffix.lower()
        self.stats['format_distribution'][file_ext] += 1
        
        # 自动处理
        if auto_process and self.enable_auto_processing:
            await self.process_document(doc_id)
        
        return doc_id
    
    async def process_document(
        self,
        doc_id: str,
        chunking_strategy: str = "sentence",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        force_reprocess: bool = False
    ) -> ProcessingResult:
        """处理文档
        
        Args:
            doc_id: 文档ID
            chunking_strategy: 分块策略
            chunk_size: 块大小
            chunk_overlap: 块重叠
            force_reprocess: 强制重新处理
            
        Returns:
            处理结果
        """
        if doc_id not in self.document_metadata:
            raise ValueError(f"文档不存在: {doc_id}")
        
        doc_metadata = self.document_metadata[doc_id]
        
        # 检查是否需要处理
        if (doc_metadata['status'] == DocumentStatus.PROCESSED.value and 
            not force_reprocess):
            return ProcessingResult(
                doc_id=doc_id,
                status="already_processed",
                chunks_created=doc_metadata['chunks_count'],
                processing_time=0.0,
                message="文档已处理"
            )
        
        start_time = datetime.now()
        
        try:
            # 更新状态
            doc_metadata['status'] = DocumentStatus.PROCESSING.value
            doc_metadata['processing_attempts'] += 1
            self.processing_status[doc_id] = "processing"
            
            # 读取文件内容
            file_path = Path(doc_metadata['file_path'])
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # 确定文档类型
            doc_type = self._determine_document_type(doc_metadata['filename'])
            
            # 创建文档对象
            document = Document(
                doc_id=doc_id,
                content=file_content.decode('utf-8', errors='ignore'),
                doc_type=doc_type,
                metadata={
                    **doc_metadata['metadata'],
                    'filename': doc_metadata['filename'],
                    'upload_time': doc_metadata['upload_time'],
                    'file_size': doc_metadata['file_size'],
                    'user_id': doc_metadata['user_id']
                }
            )
            
            # 处理文档
            if self.rag_engine:
                # 配置处理参数
                processing_config: Dict[str, Any] = {
                    'chunking_strategy': ChunkingStrategy(chunking_strategy),
                    'chunk_size': chunk_size,
                    'chunk_overlap': chunk_overlap
                }

                # 如果适配器可用，尝试预处理并直通预计算块
                precomputed_chunks: List[Dict[str, Any]] = []
                adapter_used = False
                if self.adapter and getattr(self.adapter, 'enabled', False):
                    try:
                        precomputed_chunks = self.adapter.process_document(str(file_path), force_reprocess=force_reprocess)
                        if precomputed_chunks:
                            processing_config['precomputed_chunks'] = precomputed_chunks
                            adapter_used = True
                    except Exception:
                        # 适配器失败则回退到常规路径
                        precomputed_chunks = []
                        adapter_used = False
                
                # 添加到RAG引擎（带重试）
                result = await retry_async(
                    self.rag_engine.add_document,
                    attempts=3,
                    base_delay=0.5,
                    max_delay=3.0,
                    exceptions=(RAGError, Exception),
                    document=document,
                    config=processing_config
                )
                
                chunks_created = len(result.get('chunks', []))

                # 记录适配器使用情况与块数
                doc_metadata['adapter_used'] = adapter_used
                if adapter_used:
                    doc_metadata['adapter_pre_chunks'] = len(precomputed_chunks)
                    doc_metadata['adapter_enabled'] = True
                else:
                    doc_metadata['adapter_enabled'] = bool(self.adapter and getattr(self.adapter, 'enabled', False))
            else:
                # 模拟处理
                chunks_created = max(1, len(document.content) // chunk_size)
            
            # 更新元数据
            processing_time = (datetime.now() - start_time).total_seconds()
            doc_metadata.update({
                'status': DocumentStatus.PROCESSED.value,
                'processing_time': processing_time,
                'chunks_count': chunks_created,
                'chunking_strategy': chunking_strategy,
                'chunk_size': chunk_size,
                'chunk_overlap': chunk_overlap,
                'processed_time': datetime.now().isoformat()
            })
            
            # 更新统计信息
            self.stats['processing_success'] += 1
            self.stats['total_chunks'] += chunks_created
            self.stats['processing_time'][doc_type.value] += processing_time
            
            # 保存元数据
            await self._save_metadata()
            
            # 更新处理状态
            self.processing_status[doc_id] = "completed"
            
            return ProcessingResult(
                doc_id=doc_id,
                status="success",
                chunks_created=chunks_created,
                processing_time=processing_time,
                message="文档处理成功"
            )
            
        except Exception as e:
            # 处理失败
            doc_metadata['status'] = DocumentStatus.FAILED.value
            doc_metadata['error_message'] = str(e)
            doc_metadata['failed_time'] = datetime.now().isoformat()
            
            self.stats['processing_failed'] += 1
            self.processing_status[doc_id] = "failed"
            
            await self._save_metadata()
            
            return ProcessingResult(
                doc_id=doc_id,
                status="failed",
                chunks_created=0,
                processing_time=(datetime.now() - start_time).total_seconds(),
                message=f"文档处理失败: {str(e)}"
            )
    
    async def get_document_info(self, doc_id: str) -> DocumentInfo:
        """获取文档信息"""
        if doc_id not in self.document_metadata:
            raise ValueError(f"文档不存在: {doc_id}")
        
        doc_metadata = self.document_metadata[doc_id]
        
        return DocumentInfo(
            doc_id=doc_id,
            filename=doc_metadata['filename'],
            content_type=doc_metadata['content_type'],
            file_size=doc_metadata['file_size'],
            upload_time=datetime.fromisoformat(doc_metadata['upload_time']),
            status=DocumentStatus(doc_metadata['status']),
            chunks_count=doc_metadata['chunks_count'],
            processing_time=doc_metadata.get('processing_time'),
            user_id=doc_metadata.get('user_id'),
            metadata=doc_metadata.get('metadata', {}),
            tags=doc_metadata.get('tags', []),
            language=doc_metadata.get('language', 'auto')
        )
    
    async def list_documents(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[DocumentInfo]:
        """列出文档"""
        documents = []
        
        for doc_id, doc_metadata in self.document_metadata.items():
            # 应用过滤器
            if user_id and doc_metadata.get('user_id') != user_id:
                continue
            
            if status and doc_metadata['status'] != status:
                continue
            
            if tags:
                doc_tags = doc_metadata.get('tags', [])
                if not any(tag in doc_tags for tag in tags):
                    continue
            
            # 创建文档信息
            doc_info = DocumentInfo(
                doc_id=doc_id,
                filename=doc_metadata['filename'],
                content_type=doc_metadata['content_type'],
                file_size=doc_metadata['file_size'],
                upload_time=datetime.fromisoformat(doc_metadata['upload_time']),
                status=DocumentStatus(doc_metadata['status']),
                chunks_count=doc_metadata['chunks_count'],
                processing_time=doc_metadata.get('processing_time'),
                user_id=doc_metadata.get('user_id'),
                metadata=doc_metadata.get('metadata', {}),
                tags=doc_metadata.get('tags', []),
                language=doc_metadata.get('language', 'auto')
            )
            
            documents.append(doc_info)
        
        # 按上传时间倒序排序
        documents.sort(key=lambda x: x.upload_time, reverse=True)
        
        # 分页
        return documents[offset:offset + limit]
    
    async def delete_document(self, doc_id: str, user_id: Optional[str] = None) -> bool:
        """删除文档"""
        if doc_id not in self.document_metadata:
            raise ValueError(f"文档不存在: {doc_id}")
        
        doc_metadata = self.document_metadata[doc_id]
        
        # 检查权限
        if user_id and doc_metadata.get('user_id') != user_id:
            raise PermissionError("无权限删除此文档")
        
        try:
            # 从RAG引擎删除
            if self.rag_engine:
                await self.rag_engine.delete_document(doc_id)
            
            # 删除文件
            file_path = Path(doc_metadata['file_path'])
            if file_path.exists():
                file_path.unlink()
            
            # 更新统计信息
            self.stats['total_documents'] -= 1
            self.stats['total_size'] -= doc_metadata['file_size']
            self.stats['total_chunks'] -= doc_metadata['chunks_count']
            
            file_ext = Path(doc_metadata['filename']).suffix.lower()
            self.stats['format_distribution'][file_ext] -= 1
            
            # 删除元数据
            del self.document_metadata[doc_id]
            
            # 清理处理状态
            if doc_id in self.processing_status:
                del self.processing_status[doc_id]
            
            # 保存元数据
            await self._save_metadata()
            
            return True
            
        except Exception as e:
            raise Exception(f"删除文档失败: {str(e)}")
    
    async def update_document_metadata(
        self,
        doc_id: str,
        metadata: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> bool:
        """更新文档元数据"""
        if doc_id not in self.document_metadata:
            raise ValueError(f"文档不存在: {doc_id}")
        
        doc_metadata = self.document_metadata[doc_id]
        
        # 检查权限
        if user_id and doc_metadata.get('user_id') != user_id:
            raise PermissionError("无权限修改此文档")
        
        # 更新元数据
        doc_metadata['metadata'].update(metadata)
        
        # 更新标签和语言（如果提供）
        if 'tags' in metadata:
            doc_metadata['tags'] = metadata['tags']
        
        if 'language' in metadata:
            doc_metadata['language'] = metadata['language']
        
        doc_metadata['updated_time'] = datetime.now().isoformat()
        
        # 保存元数据
        await self._save_metadata()
        
        return True
    
    async def get_document_content(
        self,
        doc_id: str,
        user_id: Optional[str] = None
    ) -> str:
        """获取文档内容"""
        if doc_id not in self.document_metadata:
            raise ValueError(f"文档不存在: {doc_id}")
        
        doc_metadata = self.document_metadata[doc_id]
        
        # 检查权限
        if user_id and doc_metadata.get('user_id') != user_id:
            raise PermissionError("无权限访问此文档")
        
        # 读取文件内容
        file_path = Path(doc_metadata['file_path'])
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    async def get_document_chunks(
        self,
        doc_id: str,
        user_id: Optional[str] = None
    ) -> List[DocumentChunk]:
        """获取文档块"""
        if doc_id not in self.document_metadata:
            raise ValueError(f"文档不存在: {doc_id}")
        
        doc_metadata = self.document_metadata[doc_id]
        
        # 检查权限
        if user_id and doc_metadata.get('user_id') != user_id:
            raise PermissionError("无权限访问此文档")
        
        # 从RAG引擎获取块
        if self.rag_engine:
            # 统一使用向量存储的 list_chunks 接口按 doc_id 过滤
            chunks = await self.rag_engine.vector_store.list_chunks(doc_id=doc_id)
            return chunks
        else:
            return []
    
    async def search_documents(
        self,
        query: str,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[DocumentInfo]:
        """搜索文档"""
        results = []
        query_lower = query.lower()
        
        for doc_id, doc_metadata in self.document_metadata.items():
            # 检查权限
            if user_id and doc_metadata.get('user_id') != user_id:
                continue
            
            # 应用过滤器
            if filters:
                if not self._apply_document_filters(doc_metadata, filters):
                    continue
            
            # 搜索匹配
            if (query_lower in doc_metadata['filename'].lower() or
                query_lower in str(doc_metadata.get('metadata', {})).lower() or
                any(query_lower in tag.lower() for tag in doc_metadata.get('tags', []))):
                
                doc_info = DocumentInfo(
                    doc_id=doc_id,
                    filename=doc_metadata['filename'],
                    content_type=doc_metadata['content_type'],
                    file_size=doc_metadata['file_size'],
                    upload_time=datetime.fromisoformat(doc_metadata['upload_time']),
                    status=DocumentStatus(doc_metadata['status']),
                    chunks_count=doc_metadata['chunks_count'],
                    processing_time=doc_metadata.get('processing_time'),
                    user_id=doc_metadata.get('user_id'),
                    metadata=doc_metadata.get('metadata', {}),
                    tags=doc_metadata.get('tags', []),
                    language=doc_metadata.get('language', 'auto')
                )
                
                results.append(doc_info)
        
        return results
    
    def _apply_document_filters(self, doc_metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """应用文档过滤器"""
        for key, value in filters.items():
            if key == 'status':
                if doc_metadata['status'] != value:
                    return False
            elif key == 'content_type':
                if doc_metadata['content_type'] != value:
                    return False
            elif key == 'tags':
                doc_tags = doc_metadata.get('tags', [])
                if not any(tag in doc_tags for tag in value):
                    return False
            elif key == 'language':
                if doc_metadata.get('language') != value:
                    return False
            elif key == 'file_size_min':
                if doc_metadata['file_size'] < value:
                    return False
            elif key == 'file_size_max':
                if doc_metadata['file_size'] > value:
                    return False
            elif key == 'upload_date_from':
                upload_time = datetime.fromisoformat(doc_metadata['upload_time'])
                if upload_time < datetime.fromisoformat(value):
                    return False
            elif key == 'upload_date_to':
                upload_time = datetime.fromisoformat(doc_metadata['upload_time'])
                if upload_time > datetime.fromisoformat(value):
                    return False
        return True
    
    async def get_processing_status(self, doc_id: str) -> Dict[str, Any]:
        """获取处理状态"""
        if doc_id not in self.document_metadata:
            raise ValueError(f"文档不存在: {doc_id}")
        
        doc_metadata = self.document_metadata[doc_id]
        processing_status = self.processing_status.get(doc_id, "unknown")
        
        return {
            'doc_id': doc_id,
            'status': doc_metadata['status'],
            'processing_status': processing_status,
            'processing_attempts': doc_metadata['processing_attempts'],
            'chunks_count': doc_metadata['chunks_count'],
            'error_message': doc_metadata.get('error_message'),
            'processing_time': doc_metadata.get('processing_time'),
            'processed_time': doc_metadata.get('processed_time')
        }
    
    async def get_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        
        # 如果指定用户，计算用户特定统计
        if user_id:
            user_docs = [doc for doc in self.document_metadata.values() 
                        if doc.get('user_id') == user_id]
            
            user_stats = {
                'total_documents': len(user_docs),
                'total_size': sum(doc['file_size'] for doc in user_docs),
                'total_chunks': sum(doc['chunks_count'] for doc in user_docs),
                'status_distribution': defaultdict(int),
                'format_distribution': defaultdict(int)
            }
            
            for doc in user_docs:
                user_stats['status_distribution'][doc['status']] += 1
                file_ext = Path(doc['filename']).suffix.lower()
                user_stats['format_distribution'][file_ext] += 1
            
            stats['user_stats'] = dict(user_stats)
        
        # 计算平均处理时间
        if self.stats['processing_success'] > 0:
            total_time = sum(self.stats['processing_time'].values())
            stats['avg_processing_time'] = total_time / self.stats['processing_success']
        else:
            stats['avg_processing_time'] = 0.0
        
        # 转换为普通字典
        stats['format_distribution'] = dict(stats['format_distribution'])
        stats['processing_time'] = dict(stats['processing_time'])
        
        return stats
    
    async def _validate_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: str
    ) -> None:
        """验证文件"""
        # 检查文件大小
        if len(file_content) > self.max_file_size:
            raise ValueError(f"文件大小超过限制: {len(file_content)} > {self.max_file_size}")
        
        # 检查文件格式
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.supported_formats:
            raise ValueError(f"不支持的文件格式: {file_ext}")
        
        # 检查文件内容
        if len(file_content) == 0:
            raise ValueError("文件内容为空")
    
    def _generate_document_id(self, filename: str, content: bytes) -> str:
        """生成文档ID"""
        # 使用文件名和内容哈希生成唯一ID
        content_hash = hashlib.md5(content).hexdigest()[:8]
        timestamp = int(datetime.now().timestamp() * 1000)
        return f"doc_{timestamp}_{content_hash}"

    def _compute_content_hash(self, content: bytes) -> str:
        """计算内容哈希（MD5）"""
        return hashlib.md5(content).hexdigest()
    
    async def _save_file(self, doc_id: str, filename: str, content: bytes) -> Path:
        """保存文件"""
        # 创建文档目录
        doc_dir = self.storage_path / doc_id
        doc_dir.mkdir(exist_ok=True)
        
        # 保存文件
        file_path = doc_dir / filename
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return file_path
    
    def _determine_document_type(self, filename: str) -> DocumentType:
        """确定文档类型"""
        file_ext = Path(filename).suffix.lower()
        
        if file_ext in ['.txt', '.md']:
            return DocumentType.TEXT
        elif file_ext == '.pdf':
            return DocumentType.PDF
        elif file_ext in ['.doc', '.docx']:
            return DocumentType.WORD
        elif file_ext == '.html':
            return DocumentType.HTML
        elif file_ext == '.json':
            return DocumentType.JSON
        elif file_ext == '.csv':
            return DocumentType.CSV
        else:
            return DocumentType.TEXT  # 默认为文本
    
    def _load_metadata(self) -> None:
        """加载元数据"""
        metadata_file = self.storage_path / 'metadata.json'
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.document_metadata = data.get('documents', {})
                    self.stats = data.get('stats', self.stats)
            except Exception as e:
                print(f"加载元数据失败: {e}")
    
    async def _save_metadata(self) -> None:
        """保存元数据"""
        metadata_file = self.storage_path / 'metadata.json'
        
        data = {
            'documents': self.document_metadata,
            'stats': self.stats,
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存元数据失败: {e}")
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查存储目录
            if not self.storage_path.exists():
                return False
            
            # 检查RAG引擎
            if self.rag_engine:
                rag_health = await self.rag_engine.health_check()
                return all(rag_health.values())
            
            return True
        except Exception:
            return False