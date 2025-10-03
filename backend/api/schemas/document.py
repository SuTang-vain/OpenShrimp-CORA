#!/usr/bin/env python3
"""
文档API数据模式
定义文档相关的请求和响应数据结构

运行环境: Python 3.11+
依赖: pydantic, typing, datetime, enum
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator


class DocumentStatus(str, Enum):
    """文档状态枚举"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DELETED = "deleted"


class DocumentType(str, Enum):
    """文档类型枚举"""
    TEXT = "text"
    PDF = "pdf"
    WORD = "word"
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    OTHER = "other"


class ChunkingStrategy(str, Enum):
    """分块策略枚举"""
    FIXED_SIZE = "fixed_size"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    SEMANTIC = "semantic"
    RECURSIVE = "recursive"


class DocumentUploadRequest(BaseModel):
    """文档上传请求"""
    filename: str = Field(..., description="文件名")
    content_type: str = Field(..., description="内容类型")
    metadata: Optional[Dict[str, Any]] = Field(None, description="文档元数据")
    tags: Optional[List[str]] = Field(None, description="文档标签")
    language: Optional[str] = Field("auto", description="文档语言")
    auto_process: bool = Field(True, description="是否自动处理")
    
    @validator('filename')
    def validate_filename(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("文件名不能为空")
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            return [tag.strip() for tag in v if tag.strip()]
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "filename": "example.pdf",
                "content_type": "application/pdf",
                "metadata": {
                    "title": "示例文档",
                    "author": "张三",
                    "description": "这是一个示例文档"
                },
                "tags": ["技术文档", "AI"],
                "language": "zh-CN",
                "auto_process": True
            }
        }


class DocumentProcessRequest(BaseModel):
    """文档处理请求"""
    chunking_strategy: ChunkingStrategy = Field(ChunkingStrategy.SENTENCE, description="分块策略")
    chunk_size: int = Field(1000, ge=100, le=5000, description="块大小")
    chunk_overlap: int = Field(200, ge=0, le=1000, description="块重叠")
    force_reprocess: bool = Field(False, description="强制重新处理")
    
    @validator('chunk_overlap')
    def validate_chunk_overlap(cls, v, values):
        chunk_size = values.get('chunk_size', 1000)
        if v >= chunk_size:
            raise ValueError("块重叠不能大于等于块大小")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "chunking_strategy": "sentence",
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "force_reprocess": False
            }
        }


class DocumentInfo(BaseModel):
    """文档信息"""
    doc_id: str = Field(..., description="文档ID")
    filename: str = Field(..., description="文件名")
    content_type: str = Field(..., description="内容类型")
    file_size: int = Field(..., description="文件大小（字节）")
    upload_time: datetime = Field(..., description="上传时间")
    status: DocumentStatus = Field(..., description="文档状态")
    chunks_count: int = Field(0, description="块数量")
    processing_time: Optional[float] = Field(None, description="处理时间（秒）")
    user_id: Optional[str] = Field(None, description="用户ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="文档元数据")
    tags: Optional[List[str]] = Field(None, description="文档标签")
    language: Optional[str] = Field(None, description="文档语言")
    
    class Config:
        schema_extra = {
            "example": {
                "doc_id": "doc_1234567890_abcd1234",
                "filename": "example.pdf",
                "content_type": "application/pdf",
                "file_size": 1024000,
                "upload_time": "2024-01-01T12:00:00",
                "status": "processed",
                "chunks_count": 25,
                "processing_time": 5.2,
                "user_id": "user123",
                "metadata": {
                    "title": "示例文档",
                    "author": "张三"
                },
                "tags": ["技术文档", "AI"],
                "language": "zh-CN"
            }
        }


class ProcessingResult(BaseModel):
    """处理结果"""
    doc_id: str = Field(..., description="文档ID")
    status: str = Field(..., description="处理状态")
    chunks_created: int = Field(..., description="创建的块数量")
    processing_time: float = Field(..., description="处理时间（秒）")
    message: str = Field(..., description="处理消息")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    
    class Config:
        schema_extra = {
            "example": {
                "doc_id": "doc_1234567890_abcd1234",
                "status": "success",
                "chunks_created": 25,
                "processing_time": 5.2,
                "message": "文档处理成功"
            }
        }


class DocumentChunk(BaseModel):
    """文档块"""
    chunk_id: str = Field(..., description="块ID")
    doc_id: str = Field(..., description="文档ID")
    content: str = Field(..., description="块内容")
    chunk_index: int = Field(..., description="块索引")
    start_char: int = Field(..., description="起始字符位置")
    end_char: int = Field(..., description="结束字符位置")
    metadata: Optional[Dict[str, Any]] = Field(None, description="块元数据")
    
    class Config:
        schema_extra = {
            "example": {
                "chunk_id": "chunk_1234567890_001",
                "doc_id": "doc_1234567890_abcd1234",
                "content": "这是文档的第一个块内容...",
                "chunk_index": 0,
                "start_char": 0,
                "end_char": 500,
                "metadata": {
                    "page": 1,
                    "section": "introduction"
                }
            }
        }


class DocumentListRequest(BaseModel):
    """文档列表请求"""
    user_id: Optional[str] = Field(None, description="用户ID")
    status: Optional[DocumentStatus] = Field(None, description="文档状态")
    tags: Optional[List[str]] = Field(None, description="标签过滤")
    content_type: Optional[str] = Field(None, description="内容类型过滤")
    language: Optional[str] = Field(None, description="语言过滤")
    file_size_min: Optional[int] = Field(None, ge=0, description="最小文件大小")
    file_size_max: Optional[int] = Field(None, ge=0, description="最大文件大小")
    upload_date_from: Optional[datetime] = Field(None, description="上传日期起始")
    upload_date_to: Optional[datetime] = Field(None, description="上传日期结束")
    limit: int = Field(50, ge=1, le=100, description="返回数量限制")
    offset: int = Field(0, ge=0, description="偏移量")
    
    @validator('file_size_max')
    def validate_file_size_range(cls, v, values):
        file_size_min = values.get('file_size_min')
        if file_size_min is not None and v is not None and v < file_size_min:
            raise ValueError("最大文件大小不能小于最小文件大小")
        return v
    
    @validator('upload_date_to')
    def validate_date_range(cls, v, values):
        upload_date_from = values.get('upload_date_from')
        if upload_date_from is not None and v is not None and v < upload_date_from:
            raise ValueError("结束日期不能早于开始日期")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "status": "processed",
                "tags": ["技术文档"],
                "content_type": "application/pdf",
                "limit": 20,
                "offset": 0
            }
        }


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    documents: List[DocumentInfo] = Field(..., description="文档列表")
    total: int = Field(..., description="总数量")
    limit: int = Field(..., description="限制数量")
    offset: int = Field(..., description="偏移量")
    has_more: bool = Field(..., description="是否有更多")
    
    class Config:
        schema_extra = {
            "example": {
                "documents": [
                    {
                        "doc_id": "doc_1234567890_abcd1234",
                        "filename": "example.pdf",
                        "content_type": "application/pdf",
                        "file_size": 1024000,
                        "upload_time": "2024-01-01T12:00:00",
                        "status": "processed",
                        "chunks_count": 25
                    }
                ],
                "total": 100,
                "limit": 20,
                "offset": 0,
                "has_more": True
            }
        }


class DocumentSearchRequest(BaseModel):
    """文档搜索请求"""
    query: str = Field(..., min_length=1, description="搜索查询")
    user_id: Optional[str] = Field(None, description="用户ID")
    filters: Optional[Dict[str, Any]] = Field(None, description="搜索过滤器")
    limit: int = Field(20, ge=1, le=100, description="返回数量限制")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "人工智能",
                "filters": {
                    "status": "processed",
                    "tags": ["技术文档"]
                },
                "limit": 20
            }
        }


class DocumentUpdateRequest(BaseModel):
    """文档更新请求"""
    metadata: Optional[Dict[str, Any]] = Field(None, description="更新的元数据")
    tags: Optional[List[str]] = Field(None, description="更新的标签")
    language: Optional[str] = Field(None, description="更新的语言")
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            return [tag.strip() for tag in v if tag.strip()]
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "metadata": {
                    "title": "更新的标题",
                    "description": "更新的描述"
                },
                "tags": ["更新标签", "新标签"],
                "language": "zh-CN"
            }
        }


class DocumentStats(BaseModel):
    """文档统计信息"""
    total_documents: int = Field(..., description="总文档数")
    total_chunks: int = Field(..., description="总块数")
    total_size: int = Field(..., description="总大小（字节）")
    processing_success: int = Field(..., description="处理成功数")
    processing_failed: int = Field(..., description="处理失败数")
    avg_processing_time: float = Field(..., description="平均处理时间（秒）")
    format_distribution: Dict[str, int] = Field(..., description="格式分布")
    status_distribution: Optional[Dict[str, int]] = Field(None, description="状态分布")
    user_stats: Optional[Dict[str, Any]] = Field(None, description="用户统计")
    
    class Config:
        schema_extra = {
            "example": {
                "total_documents": 150,
                "total_chunks": 3750,
                "total_size": 52428800,
                "processing_success": 145,
                "processing_failed": 5,
                "avg_processing_time": 4.2,
                "format_distribution": {
                    ".pdf": 80,
                    ".txt": 40,
                    ".docx": 30
                },
                "status_distribution": {
                    "processed": 145,
                    "failed": 5
                }
            }
        }


class ProcessingStatus(BaseModel):
    """处理状态"""
    doc_id: str = Field(..., description="文档ID")
    status: DocumentStatus = Field(..., description="文档状态")
    processing_status: str = Field(..., description="处理状态")
    processing_attempts: int = Field(..., description="处理尝试次数")
    chunks_count: int = Field(..., description="块数量")
    error_message: Optional[str] = Field(None, description="错误消息")
    processing_time: Optional[float] = Field(None, description="处理时间（秒）")
    processed_time: Optional[str] = Field(None, description="处理完成时间")
    
    class Config:
        schema_extra = {
            "example": {
                "doc_id": "doc_1234567890_abcd1234",
                "status": "processed",
                "processing_status": "completed",
                "processing_attempts": 1,
                "chunks_count": 25,
                "processing_time": 5.2,
                "processed_time": "2024-01-01T12:05:00"
            }
        }


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    doc_id: str = Field(..., description="文档ID")
    filename: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小")
    status: DocumentStatus = Field(..., description="文档状态")
    upload_time: datetime = Field(..., description="上传时间")
    processing_started: bool = Field(..., description="是否开始处理")
    message: str = Field(..., description="响应消息")
    
    class Config:
        schema_extra = {
            "example": {
                "doc_id": "doc_1234567890_abcd1234",
                "filename": "example.pdf",
                "file_size": 1024000,
                "status": "uploaded",
                "upload_time": "2024-01-01T12:00:00",
                "processing_started": True,
                "message": "文档上传成功，开始处理"
            }
        }


class BulkOperationRequest(BaseModel):
    """批量操作请求"""
    doc_ids: List[str] = Field(..., min_items=1, max_items=100, description="文档ID列表")
    operation: str = Field(..., description="操作类型")
    parameters: Optional[Dict[str, Any]] = Field(None, description="操作参数")
    
    class Config:
        schema_extra = {
            "example": {
                "doc_ids": ["doc_123", "doc_456", "doc_789"],
                "operation": "reprocess",
                "parameters": {
                    "chunking_strategy": "sentence",
                    "chunk_size": 1000
                }
            }
        }


class BulkOperationResponse(BaseModel):
    """批量操作响应"""
    operation: str = Field(..., description="操作类型")
    total_requested: int = Field(..., description="请求总数")
    successful: int = Field(..., description="成功数量")
    failed: int = Field(..., description="失败数量")
    results: List[Dict[str, Any]] = Field(..., description="详细结果")
    
    class Config:
        schema_extra = {
            "example": {
                "operation": "reprocess",
                "total_requested": 3,
                "successful": 2,
                "failed": 1,
                "results": [
                    {"doc_id": "doc_123", "status": "success"},
                    {"doc_id": "doc_456", "status": "success"},
                    {"doc_id": "doc_789", "status": "failed", "error": "文档不存在"}
                ]
            }
        }


class DocumentUploadBatchResponse(BaseModel):
    """批量文档上传响应（兼容前端期望结构）"""
    documents: List[DocumentInfo] = Field(..., description="成功上传的文档列表")
    failed: List[Dict[str, Any]] = Field(default_factory=list, description="失败项，包含文件名与错误信息")

    class Config:
        schema_extra = {
            "example": {
                "documents": [
                    {
                        "doc_id": "doc_1234567890_abcd1234",
                        "filename": "example.pdf",
                        "content_type": "application/pdf",
                        "file_size": 1024000,
                        "upload_time": "2024-01-01T12:00:00",
                        "status": "processed",
                        "chunks_count": 25
                    }
                ],
                "failed": [
                    {"filename": "bad.docx", "error": "格式不支持"}
                ]
            }
        }


class DocumentListFrontendResponse(BaseModel):
    """文档列表响应（兼容前端期望字段）"""
    documents: List[DocumentInfo] = Field(..., description="文档列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页")
    limit: int = Field(..., description="每页数量")
    totalPages: int = Field(..., description="总页数")

    class Config:
        schema_extra = {
            "example": {
                "documents": [
                    {
                        "doc_id": "doc_1234567890_abcd1234",
                        "filename": "example.pdf",
                        "content_type": "application/pdf",
                        "file_size": 1024000,
                        "upload_time": "2024-01-01T12:00:00",
                        "status": "processed",
                        "chunks_count": 25
                    }
                ],
                "total": 100,
                "page": 1,
                "limit": 20,
                "totalPages": 5
            }
        }