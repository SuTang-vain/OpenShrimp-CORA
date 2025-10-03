#!/usr/bin/env python3
"""
文档API路由
提供文档管理相关的API端点

运行环境: Python 3.11+
依赖: fastapi, typing, datetime
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status as http_status
from fastapi.responses import StreamingResponse

from backend.api.schemas.document import (
    DocumentUploadRequest, DocumentUploadResponse, DocumentProcessRequest,
    DocumentInfo, ProcessingResult, DocumentListRequest, DocumentListResponse,
    DocumentSearchRequest, DocumentUpdateRequest, DocumentStats,
    ProcessingStatus, BulkOperationRequest, BulkOperationResponse,
    DocumentChunk, DocumentStatus,
    DocumentUploadBatchResponse, DocumentListFrontendResponse
)
from backend.api.dependencies.services import get_document_service
from backend.api.dependencies.auth import get_current_user, get_optional_user
from backend.services.document.service import DocumentService


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadBatchResponse)
async def upload_document(
    files: Optional[List[UploadFile]] = File(None),
    file: Optional[UploadFile] = File(None),
    metadata: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    language: Optional[str] = Form("auto"),
    auto_process: bool = Form(True),
    document_service: DocumentService = Depends(get_document_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """上传文档（支持批量）
    
    - 兼容旧字段 `file`
    - 新字段 `files` 支持多文件上传
    - 返回批量上传响应，包含成功与失败项
    """
    try:
        # 整理文件列表
        upload_files: List[UploadFile] = []
        if files:
            upload_files.extend([f for f in files if f and f.filename])
        if file and file.filename:
            upload_files.append(file)
        
        if not upload_files:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="没有文件被上传"
            )
        
        # 解析元数据和标签
        parsed_metadata: Dict[str, Any] = {}
        if metadata:
            try:
                import json
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="元数据格式无效"
                )
        
        parsed_tags: List[str] = []
        if tags:
            parsed_tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
        if parsed_tags:
            parsed_metadata['tags'] = parsed_tags
        
        successes: List[DocumentInfo] = []
        failures: List[Dict[str, str]] = []
        
        # 逐个处理文件
        for f in upload_files:
            try:
                content = await f.read()
                doc_id = await document_service.upload_document(
                    file_content=content,
                    filename=f.filename,
                    content_type=f.content_type,
                    metadata=parsed_metadata,
                    user_id=current_user.get('user_id') if current_user else None,
                    auto_process=auto_process
                )
                info = await document_service.get_document_info(doc_id)
                successes.append(info)
            except Exception as fe:
                failures.append({
                    "filename": f.filename or "unknown",
                    "error": str(fe)
                })
        
        return DocumentUploadBatchResponse(
            documents=successes,
            failed=failures
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档上传失败: {str(e)}"
        )


@router.post("", response_model=DocumentUploadBatchResponse)
async def upload_document_root(
    files: Optional[List[UploadFile]] = File(None),
    file: Optional[UploadFile] = File(None),
    metadata: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    language: Optional[str] = Form("auto"),
    auto_process: bool = Form(True),
    document_service: DocumentService = Depends(get_document_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """根路径上传文档（与 /upload 行为一致）"""
    return await upload_document(
        files=files,
        file=file,
        metadata=metadata,
        tags=tags,
        language=language,
        auto_process=auto_process,
        document_service=document_service,
        current_user=current_user
    )


@router.post("/{doc_id}/process", response_model=ProcessingResult)
async def process_document(
    doc_id: str,
    request: DocumentProcessRequest,
    document_service: DocumentService = Depends(get_document_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """处理文档
    
    对已上传的文档进行分块和向量化处理
    """
    try:
        # 检查文档权限
        doc_info = await document_service.get_document_info(doc_id)
        if (current_user and doc_info.user_id and 
            doc_info.user_id != current_user.get('user_id')):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限处理此文档"
            )
        
        # 处理文档
        result = await document_service.process_document(
            doc_id=doc_id,
            chunking_strategy=request.chunking_strategy.value,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            force_reprocess=request.force_reprocess
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档处理失败: {str(e)}"
        )


@router.get("/{doc_id}", response_model=DocumentInfo)
async def get_document(
    doc_id: str,
    document_service: DocumentService = Depends(get_document_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """获取文档信息"""
    try:
        doc_info = await document_service.get_document_info(doc_id)
        
        # 检查权限
        if (current_user and doc_info.user_id and 
            doc_info.user_id != current_user.get('user_id')):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此文档"
            )
        
        return doc_info
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get("/", response_model=DocumentListFrontendResponse)
@router.get("", response_model=DocumentListFrontendResponse)
async def list_documents(
    user_id: Optional[str] = Query(None),
    status: Optional[DocumentStatus] = Query(None),
    tags: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    file_size_min: Optional[int] = Query(None, ge=0),
    file_size_max: Optional[int] = Query(None, ge=0),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    document_service: DocumentService = Depends(get_document_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """列出文档
    
    支持多种过滤条件和分页（page/limit），返回 totalPages
    """
    try:
        # 解析标签
        parsed_tags = None
        if tags:
            parsed_tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # 如果用户已登录但没有指定user_id，默认查询当前用户的文档
        query_user_id = user_id
        if current_user and not user_id:
            query_user_id = current_user.get('user_id')
        
        # 计算偏移量
        offset = (page - 1) * limit
        
        # 获取所有匹配的文档用于计算总数
        all_docs = await document_service.list_documents(
            user_id=query_user_id,
            status=status.value if status else None,
            tags=parsed_tags,
            limit=100000,
            offset=0
        )
        total = len(all_docs)
        total_pages = (total + limit - 1) // limit
        
        # 获取当前页文档
        documents = all_docs[offset: offset + limit]
        
        return DocumentListFrontendResponse(
            documents=documents,
            total=total,
            page=page,
            limit=limit,
            totalPages=total_pages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档列表失败: {str(e)}"
        )


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    document_service: DocumentService = Depends(get_document_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """删除文档"""
    try:
        success = await document_service.delete_document(
            doc_id=doc_id,
            user_id=current_user.get('user_id') if current_user else None
        )
        
        if success:
            return {"message": "文档删除成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="文档删除失败"
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档删除失败: {str(e)}"
        )


@router.put("/{doc_id}", response_model=DocumentInfo)
async def update_document(
    doc_id: str,
    request: DocumentUpdateRequest,
    document_service: DocumentService = Depends(get_document_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """更新文档元数据"""
    try:
        # 构建更新数据
        update_data = {}
        if request.metadata is not None:
            update_data.update(request.metadata)
        if request.tags is not None:
            update_data['tags'] = request.tags
        if request.language is not None:
            update_data['language'] = request.language
        
        # 更新文档
        success = await document_service.update_document_metadata(
            doc_id=doc_id,
            metadata=update_data,
            user_id=current_user.get('user_id') if current_user else None
        )
        
        if success:
            # 返回更新后的文档信息
            return await document_service.get_document_info(doc_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="文档更新失败"
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档更新失败: {str(e)}"
        )


@router.get("/{doc_id}/content")
async def get_document_content(
    doc_id: str,
    document_service: DocumentService = Depends(get_document_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """获取文档内容"""
    try:
        content = await document_service.get_document_content(
            doc_id=doc_id,
            user_id=current_user.get('user_id') if current_user else None
        )
        
        return {"content": content}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档内容失败: {str(e)}"
        )


@router.get("/{doc_id}/chunks", response_model=List[DocumentChunk])
async def get_document_chunks(
    doc_id: str,
    document_service: DocumentService = Depends(get_document_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """获取文档块"""
    try:
        chunks = await document_service.get_document_chunks(
            doc_id=doc_id,
            user_id=current_user.get('user_id') if current_user else None
        )
        
        # 转换为API响应格式
        chunk_responses = []
        for chunk in chunks:
            chunk_response = DocumentChunk(
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                metadata=chunk.metadata
            )
            chunk_responses.append(chunk_response)
        
        return chunk_responses
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档块失败: {str(e)}"
        )


@router.post("/search", response_model=List[DocumentInfo])
async def search_documents(
    request: DocumentSearchRequest,
    document_service: DocumentService = Depends(get_document_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """搜索文档
    
    基于文档元数据和内容进行搜索
    """
    try:
        # 如果用户已登录但没有指定user_id，默认搜索当前用户的文档
        query_user_id = request.user_id
        if current_user and not request.user_id:
            query_user_id = current_user.get('user_id')
        
        documents = await document_service.search_documents(
            query=request.query,
            user_id=query_user_id,
            filters=request.filters
        )
        
        # 限制返回数量
        return documents[:request.limit]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档搜索失败: {str(e)}"
        )


@router.get("/{doc_id}/status", response_model=ProcessingStatus)
async def get_processing_status(
    doc_id: str,
    document_service: DocumentService = Depends(get_document_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """获取文档处理状态"""
    try:
        # 检查权限
        doc_info = await document_service.get_document_info(doc_id)
        if (current_user and doc_info.user_id and 
            doc_info.user_id != current_user.get('user_id')):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此文档"
            )
        
        status_info = await document_service.get_processing_status(doc_id)
        
        return ProcessingStatus(
            doc_id=status_info['doc_id'],
            status=DocumentStatus(status_info['status']),
            processing_status=status_info['processing_status'],
            processing_attempts=status_info['processing_attempts'],
            chunks_count=status_info['chunks_count'],
            error_message=status_info.get('error_message'),
            processing_time=status_info.get('processing_time'),
            processed_time=status_info.get('processed_time')
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取处理状态失败: {str(e)}"
        )


@router.get("/stats/overview", response_model=DocumentStats)
async def get_document_stats(
    user_id: Optional[str] = Query(None),
    document_service: DocumentService = Depends(get_document_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """获取文档统计信息"""
    try:
        # 如果用户已登录但没有指定user_id，默认查询当前用户的统计
        query_user_id = user_id
        if current_user and not user_id:
            query_user_id = current_user.get('user_id')
        
        stats = await document_service.get_stats(user_id=query_user_id)
        
        return DocumentStats(
            total_documents=stats['total_documents'],
            total_chunks=stats['total_chunks'],
            total_size=stats['total_size'],
            processing_success=stats['processing_success'],
            processing_failed=stats['processing_failed'],
            avg_processing_time=stats['avg_processing_time'],
            format_distribution=stats['format_distribution'],
            status_distribution=stats.get('status_distribution'),
            user_stats=stats.get('user_stats')
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.post("/bulk", response_model=BulkOperationResponse)
async def bulk_operation(
    request: BulkOperationRequest,
    document_service: DocumentService = Depends(get_document_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """批量操作文档
    
    支持批量删除、重新处理等操作
    """
    try:
        results = []
        successful = 0
        failed = 0
        
        for doc_id in request.doc_ids:
            try:
                if request.operation == "delete":
                    success = await document_service.delete_document(
                        doc_id=doc_id,
                        user_id=current_user.get('user_id') if current_user else None
                    )
                    if success:
                        results.append({"doc_id": doc_id, "status": "success"})
                        successful += 1
                    else:
                        results.append({"doc_id": doc_id, "status": "failed", "error": "删除失败"})
                        failed += 1
                        
                elif request.operation == "reprocess":
                    params = request.parameters or {}
                    result = await document_service.process_document(
                        doc_id=doc_id,
                        chunking_strategy=params.get('chunking_strategy', 'sentence'),
                        chunk_size=params.get('chunk_size', 1000),
                        chunk_overlap=params.get('chunk_overlap', 200),
                        force_reprocess=True
                    )
                    if result.status == "success":
                        results.append({"doc_id": doc_id, "status": "success"})
                        successful += 1
                    else:
                        results.append({"doc_id": doc_id, "status": "failed", "error": result.message})
                        failed += 1
                        
                else:
                    results.append({"doc_id": doc_id, "status": "failed", "error": "不支持的操作"})
                    failed += 1
                    
            except Exception as e:
                results.append({"doc_id": doc_id, "status": "failed", "error": str(e)})
                failed += 1
        
        return BulkOperationResponse(
            operation=request.operation,
            total_requested=len(request.doc_ids),
            successful=successful,
            failed=failed,
            results=results
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量操作失败: {str(e)}"
        )