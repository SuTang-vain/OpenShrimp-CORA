#!/usr/bin/env python3
"""
文档服务管理器
管理文档的上传、处理和存储

运行环境: Python 3.11+
依赖: typing, pathlib, asyncio
"""

import os
import asyncio
from typing import Dict, Any, List, Optional, BinaryIO
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import hashlib
import mimetypes


@dataclass
class DocumentInfo:
    """文档信息"""
    document_id: str
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    file_hash: str
    status: str = "uploaded"  # uploaded, processing, processed, failed
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    processed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class DocumentService:
    """文档服务"""
    
    def __init__(self, upload_dir: str = "./data/uploads", backup_dir: str = "./data/backups"):
        self.upload_dir = Path(upload_dir)
        self.backup_dir = Path(backup_dir)
        self.documents: Dict[str, DocumentInfo] = {}
        self.allowed_extensions = {
            '.txt', '.pdf', '.docx', '.doc', '.html', '.htm', 
            '.md', '.json', '.csv', '.xlsx', '.xls'
        }
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
        # 确保目录存在
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def upload_document(self, filename: str, file_content: bytes) -> str:
        """上传文档
        
        Args:
            filename: 文件名
            file_content: 文件内容
            
        Returns:
            文档ID
            
        Raises:
            ValueError: 文件格式不支持或文件过大
        """
        # 验证文件扩展名
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            raise ValueError(f"不支持的文件格式: {file_ext}")
        
        # 验证文件大小
        if len(file_content) > self.max_file_size:
            raise ValueError(f"文件过大: {len(file_content)} bytes > {self.max_file_size} bytes")
        
        # 生成文件哈希
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # 检查是否已存在相同文件
        existing_doc = self._find_document_by_hash(file_hash)
        if existing_doc:
            return existing_doc.document_id
        
        # 生成文档ID和文件路径
        document_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        safe_filename = self._sanitize_filename(filename)
        file_path = self.upload_dir / f"{document_id}_{safe_filename}"
        
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # 获取MIME类型
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        # 创建文档信息
        doc_info = DocumentInfo(
            document_id=document_id,
            filename=filename,
            file_path=str(file_path),
            file_size=len(file_content),
            mime_type=mime_type,
            file_hash=file_hash
        )
        
        self.documents[document_id] = doc_info
        
        # 异步处理文档
        asyncio.create_task(self._process_document(doc_info))
        
        return document_id
    
    async def get_document(self, document_id: str) -> Optional[DocumentInfo]:
        """获取文档信息
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档信息或None
        """
        return self.documents.get(document_id)
    
    async def list_documents(self, status: Optional[str] = None, limit: int = 100) -> List[DocumentInfo]:
        """列出文档
        
        Args:
            status: 状态过滤
            limit: 返回数量限制
            
        Returns:
            文档列表
        """
        docs = list(self.documents.values())
        
        if status:
            docs = [doc for doc in docs if doc.status == status]
        
        # 按创建时间倒序排列
        docs.sort(key=lambda x: x.created_at, reverse=True)
        
        return docs[:limit]
    
    async def delete_document(self, document_id: str) -> bool:
        """删除文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            是否成功删除
        """
        if document_id not in self.documents:
            return False
        
        doc_info = self.documents[document_id]
        
        # 删除文件
        try:
            file_path = Path(doc_info.file_path)
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass  # 忽略文件删除错误
        
        # 从内存中删除
        del self.documents[document_id]
        
        return True
    
    async def get_document_content(self, document_id: str) -> Optional[bytes]:
        """获取文档内容
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档内容或None
        """
        doc_info = self.documents.get(document_id)
        if not doc_info:
            return None
        
        try:
            with open(doc_info.file_path, 'rb') as f:
                return f.read()
        except Exception:
            return None
    
    async def update_document_metadata(self, document_id: str, metadata: Dict[str, Any]) -> bool:
        """更新文档元数据
        
        Args:
            document_id: 文档ID
            metadata: 元数据
            
        Returns:
            是否成功更新
        """
        if document_id not in self.documents:
            return False
        
        doc_info = self.documents[document_id]
        doc_info.metadata.update(metadata)
        
        return True
    
    async def _process_document(self, doc_info: DocumentInfo):
        """处理文档
        
        Args:
            doc_info: 文档信息
        """
        try:
            doc_info.status = "processing"
            
            # 模拟文档处理
            await asyncio.sleep(2)
            
            # 根据文件类型进行不同处理
            if doc_info.mime_type.startswith('text/'):
                await self._process_text_document(doc_info)
            elif doc_info.mime_type == 'application/pdf':
                await self._process_pdf_document(doc_info)
            elif doc_info.mime_type.startswith('application/vnd.openxmlformats'):
                await self._process_office_document(doc_info)
            else:
                await self._process_generic_document(doc_info)
            
            doc_info.status = "processed"
            doc_info.processed_at = datetime.now()
            
        except Exception as e:
            doc_info.status = "failed"
            doc_info.metadata["error"] = str(e)
    
    async def _process_text_document(self, doc_info: DocumentInfo):
        """处理文本文档
        
        Args:
            doc_info: 文档信息
        """
        try:
            with open(doc_info.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            doc_info.metadata.update({
                "content_length": len(content),
                "line_count": content.count('\n') + 1,
                "word_count": len(content.split())
            })
        except Exception as e:
            doc_info.metadata["processing_error"] = str(e)
    
    async def _process_pdf_document(self, doc_info: DocumentInfo):
        """处理PDF文档
        
        Args:
            doc_info: 文档信息
        """
        # 模拟PDF处理
        doc_info.metadata.update({
            "page_count": 10,  # 模拟页数
            "has_text": True,
            "has_images": False
        })
    
    async def _process_office_document(self, doc_info: DocumentInfo):
        """处理Office文档
        
        Args:
            doc_info: 文档信息
        """
        # 模拟Office文档处理
        doc_info.metadata.update({
            "page_count": 5,  # 模拟页数
            "has_tables": True,
            "has_images": False
        })
    
    async def _process_generic_document(self, doc_info: DocumentInfo):
        """处理通用文档
        
        Args:
            doc_info: 文档信息
        """
        # 通用处理
        doc_info.metadata.update({
            "processed_type": "generic"
        })
    
    def _find_document_by_hash(self, file_hash: str) -> Optional[DocumentInfo]:
        """根据哈希查找文档
        
        Args:
            file_hash: 文件哈希
            
        Returns:
            文档信息或None
        """
        for doc_info in self.documents.values():
            if doc_info.file_hash == file_hash:
                return doc_info
        return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # 移除或替换不安全字符
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        # 限制长度
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:100-len(ext)] + ext
        
        return filename
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息
        """
        status_counts = {}
        total_size = 0
        
        for doc_info in self.documents.values():
            status_counts[doc_info.status] = status_counts.get(doc_info.status, 0) + 1
            total_size += doc_info.file_size
        
        return {
            "total_documents": len(self.documents),
            "total_size_bytes": total_size,
            "status_breakdown": status_counts,
            "allowed_extensions": list(self.allowed_extensions),
            "max_file_size_bytes": self.max_file_size
        }


# 全局实例
_document_service = None


def get_document_service() -> DocumentService:
    """获取文档服务实例（单例模式）
    
    Returns:
        文档服务实例
    """
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service