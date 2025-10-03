#!/usr/bin/env python3
"""
统一响应工具模块
提供标准化的API响应格式

运行环境: Python 3.11+
依赖: typing, datetime
"""

from typing import Any, Optional, Dict, List
from datetime import datetime
from fastapi import HTTPException
from fastapi.responses import JSONResponse


def create_success_response(
    data: Any = None,
    message: str = "操作成功",
    code: int = 200,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """创建成功响应
    
    Args:
        data: 响应数据
        message: 响应消息
        code: 状态码
        metadata: 元数据
        
    Returns:
        标准化的成功响应
    """
    response = {
        "success": True,
        "code": code,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    
    if metadata:
        response["metadata"] = metadata
    
    return response


def create_error_response(
    message: str = "操作失败",
    code: int = 500,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None
) -> Dict[str, Any]:
    """创建错误响应
    
    Args:
        message: 错误消息
        code: HTTP状态码
        error_code: 业务错误码
        details: 错误详情
        trace_id: 追踪ID
        
    Returns:
        标准化的错误响应
    """
    response = {
        "success": False,
        "code": code,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "data": None
    }
    
    if error_code:
        response["error_code"] = error_code
    
    if details:
        response["details"] = details
    
    if trace_id:
        response["trace_id"] = trace_id
    
    return response


def create_paginated_response(
    items: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
    message: str = "查询成功"
) -> Dict[str, Any]:
    """创建分页响应
    
    Args:
        items: 数据项列表
        total: 总数量
        page: 当前页码
        page_size: 每页大小
        message: 响应消息
        
    Returns:
        标准化的分页响应
    """
    total_pages = (total + page_size - 1) // page_size
    has_next = page < total_pages
    has_prev = page > 1
    
    pagination = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_prev": has_prev
    }
    
    return create_success_response(
        data={
            "items": items,
            "pagination": pagination
        },
        message=message
    )


def create_validation_error_response(
    errors: List[Dict[str, Any]],
    message: str = "参数验证失败"
) -> Dict[str, Any]:
    """创建参数验证错误响应
    
    Args:
        errors: 验证错误列表
        message: 错误消息
        
    Returns:
        标准化的验证错误响应
    """
    return create_error_response(
        message=message,
        code=422,
        error_code="VALIDATION_ERROR",
        details={"validation_errors": errors}
    )


def create_not_found_response(
    resource: str = "资源",
    resource_id: Optional[str] = None
) -> Dict[str, Any]:
    """创建资源未找到响应
    
    Args:
        resource: 资源名称
        resource_id: 资源ID
        
    Returns:
        标准化的未找到响应
    """
    message = f"{resource}未找到"
    if resource_id:
        message += f"(ID: {resource_id})"
    
    return create_error_response(
        message=message,
        code=404,
        error_code="RESOURCE_NOT_FOUND",
        details={"resource": resource, "resource_id": resource_id}
    )


def create_unauthorized_response(
    message: str = "未授权访问"
) -> Dict[str, Any]:
    """创建未授权响应
    
    Args:
        message: 错误消息
        
    Returns:
        标准化的未授权响应
    """
    return create_error_response(
        message=message,
        code=401,
        error_code="UNAUTHORIZED"
    )


def create_forbidden_response(
    message: str = "禁止访问"
) -> Dict[str, Any]:
    """创建禁止访问响应
    
    Args:
        message: 错误消息
        
    Returns:
        标准化的禁止访问响应
    """
    return create_error_response(
        message=message,
        code=403,
        error_code="FORBIDDEN"
    )


def create_rate_limit_response(
    message: str = "请求过于频繁",
    retry_after: Optional[int] = None
) -> Dict[str, Any]:
    """创建速率限制响应
    
    Args:
        message: 错误消息
        retry_after: 重试等待时间（秒）
        
    Returns:
        标准化的速率限制响应
    """
    details = {}
    if retry_after:
        details["retry_after"] = retry_after
    
    return create_error_response(
        message=message,
        code=429,
        error_code="RATE_LIMIT_EXCEEDED",
        details=details if details else None
    )


def create_server_error_response(
    message: str = "服务器内部错误",
    error_id: Optional[str] = None
) -> Dict[str, Any]:
    """创建服务器错误响应
    
    Args:
        message: 错误消息
        error_id: 错误ID
        
    Returns:
        标准化的服务器错误响应
    """
    details = {}
    if error_id:
        details["error_id"] = error_id
    
    return create_error_response(
        message=message,
        code=500,
        error_code="INTERNAL_SERVER_ERROR",
        details=details if details else None
    )


class APIResponse:
    """API响应工具类"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "操作成功",
        status_code: int = 200
    ) -> JSONResponse:
        """返回成功的JSON响应
        
        Args:
            data: 响应数据
            message: 响应消息
            status_code: HTTP状态码
            
        Returns:
            JSONResponse对象
        """
        content = create_success_response(data=data, message=message, code=status_code)
        return JSONResponse(content=content, status_code=status_code)
    
    @staticmethod
    def error(
        message: str = "操作失败",
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """返回错误的JSON响应
        
        Args:
            message: 错误消息
            status_code: HTTP状态码
            error_code: 业务错误码
            details: 错误详情
            
        Returns:
            JSONResponse对象
        """
        content = create_error_response(
            message=message,
            code=status_code,
            error_code=error_code,
            details=details
        )
        return JSONResponse(content=content, status_code=status_code)
    
    @staticmethod
    def not_found(
        resource: str = "资源",
        resource_id: Optional[str] = None
    ) -> JSONResponse:
        """返回资源未找到响应
        
        Args:
            resource: 资源名称
            resource_id: 资源ID
            
        Returns:
            JSONResponse对象
        """
        content = create_not_found_response(resource=resource, resource_id=resource_id)
        return JSONResponse(content=content, status_code=404)
    
    @staticmethod
    def unauthorized(message: str = "未授权访问") -> JSONResponse:
        """返回未授权响应
        
        Args:
            message: 错误消息
            
        Returns:
            JSONResponse对象
        """
        content = create_unauthorized_response(message=message)
        return JSONResponse(content=content, status_code=401)
    
    @staticmethod
    def forbidden(message: str = "禁止访问") -> JSONResponse:
        """返回禁止访问响应
        
        Args:
            message: 错误消息
            
        Returns:
            JSONResponse对象
        """
        content = create_forbidden_response(message=message)
        return JSONResponse(content=content, status_code=403)
    
    @staticmethod
    def validation_error(errors: List[Dict[str, Any]]) -> JSONResponse:
        """返回参数验证错误响应
        
        Args:
            errors: 验证错误列表
            
        Returns:
            JSONResponse对象
        """
        content = create_validation_error_response(errors=errors)
        return JSONResponse(content=content, status_code=422)


# 便捷函数
def success_json(data: Any = None, message: str = "操作成功") -> JSONResponse:
    """快速创建成功响应"""
    return APIResponse.success(data=data, message=message)


def error_json(message: str, status_code: int = 500) -> JSONResponse:
    """快速创建错误响应"""
    return APIResponse.error(message=message, status_code=status_code)


def not_found_json(resource: str = "资源") -> JSONResponse:
    """快速创建未找到响应"""
    return APIResponse.not_found(resource=resource)