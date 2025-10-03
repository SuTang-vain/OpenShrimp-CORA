#!/usr/bin/env python3
"""
LLM抽象层基础模块
提供统一的LLM接口抽象

运行环境: Python 3.11+
依赖: abc, typing, dataclasses, asyncio
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid


class ModelType(Enum):
    """模型类型枚举"""
    TEXT_GENERATION = "text_generation"
    TEXT_EMBEDDING = "text_embedding"
    MULTIMODAL = "multimodal"
    CODE_GENERATION = "code_generation"
    CHAT = "chat"


class ProviderType(Enum):
    """提供者类型枚举"""
    REMOTE = "remote"
    LOCAL = "local"
    HYBRID = "hybrid"


@dataclass
class ModelInfo:
    """模型信息"""
    id: str
    name: str
    provider: str
    model_type: ModelType
    provider_type: ProviderType
    max_tokens: int = 4096
    context_length: int = 4096
    supports_streaming: bool = False
    supports_functions: bool = False
    cost_per_token: float = 0.0
    description: str = ""
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'provider': self.provider,
            'model_type': self.model_type.value,
            'provider_type': self.provider_type.value,
            'max_tokens': self.max_tokens,
            'context_length': self.context_length,
            'supports_streaming': self.supports_streaming,
            'supports_functions': self.supports_functions,
            'cost_per_token': self.cost_per_token,
            'description': self.description,
            'version': self.version,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class LLMRequest:
    """LLM请求"""
    prompt: str
    model_id: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = field(default_factory=list)
    stream: bool = False
    functions: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'prompt': self.prompt,
            'model_id': self.model_id,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'frequency_penalty': self.frequency_penalty,
            'presence_penalty': self.presence_penalty,
            'stop_sequences': self.stop_sequences,
            'stream': self.stream,
            'functions': self.functions,
            'metadata': self.metadata,
            'request_id': self.request_id,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class TokenUsage:
    """Token使用统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def __post_init__(self):
        if self.total_tokens == 0:
            self.total_tokens = self.prompt_tokens + self.completion_tokens
    
    def to_dict(self) -> Dict[str, int]:
        """转换为字典格式"""
        return {
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens
        }


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    model_id: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    latency: float = 0.0
    error: Optional[str] = None
    finish_reason: str = "stop"
    function_call: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: str = ""
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def success(self) -> bool:
        """是否成功"""
        return self.error is None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'content': self.content,
            'model_id': self.model_id,
            'usage': self.usage.to_dict(),
            'latency': self.latency,
            'error': self.error,
            'finish_reason': self.finish_reason,
            'function_call': self.function_call,
            'metadata': self.metadata,
            'request_id': self.request_id,
            'response_id': self.response_id,
            'created_at': self.created_at.isoformat(),
            'success': self.success
        }


@dataclass
class StreamChunk:
    """流式响应块"""
    content: str
    delta: str = ""
    finish_reason: Optional[str] = None
    usage: Optional[TokenUsage] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'content': self.content,
            'delta': self.delta,
            'finish_reason': self.finish_reason,
            'usage': self.usage.to_dict() if self.usage else None,
            'metadata': self.metadata,
            'chunk_id': self.chunk_id,
            'created_at': self.created_at.isoformat()
        }


class BaseLLMProvider(ABC):
    """LLM提供者基类
    
    所有LLM提供者都必须继承此基类并实现抽象方法
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化提供者
        
        Args:
            config: 提供者配置
        """
        self.config = config
        self.provider_id = str(uuid.uuid4())
        self.name = self.__class__.__name__
        self.created_at = datetime.now()
        self.request_count = 0
        self.total_tokens = 0
        self.total_latency = 0.0
        
        # 验证配置
        if not self.validate_config():
            raise ValueError(f"Invalid configuration for provider {self.name}")
    
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """生成文本
        
        Args:
            request: LLM请求
            
        Returns:
            LLMResponse: LLM响应
        """
        pass
    
    @abstractmethod
    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[StreamChunk, None]:
        """流式生成文本
        
        Args:
            request: LLM请求
            
        Yields:
            StreamChunk: 流式响应块
        """
        pass
    
    @abstractmethod
    def list_models(self) -> List[ModelInfo]:
        """列出可用模型
        
        Returns:
            List[ModelInfo]: 模型信息列表
        """
        pass
    
    @abstractmethod
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """获取模型信息
        
        Args:
            model_id: 模型ID
            
        Returns:
            Optional[ModelInfo]: 模型信息
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 是否健康
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置
        
        Returns:
            bool: 配置是否有效
        """
        pass
    
    async def _generate_with_metrics(self, request: LLMRequest) -> LLMResponse:
        """带性能监控的生成方法
        
        Args:
            request: LLM请求
            
        Returns:
            LLMResponse: LLM响应
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            response = await self.generate(request)
            latency = asyncio.get_event_loop().time() - start_time
            
            # 更新统计信息
            self.request_count += 1
            self.total_tokens += response.usage.total_tokens
            self.total_latency += latency
            response.latency = latency
            response.request_id = request.request_id
            
            return response
            
        except Exception as e:
            latency = asyncio.get_event_loop().time() - start_time
            
            return LLMResponse(
                content="",
                model_id=request.model_id or "unknown",
                error=str(e),
                latency=latency,
                request_id=request.request_id
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取提供者统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        avg_latency = (
            self.total_latency / self.request_count 
            if self.request_count > 0 else 0.0
        )
        
        avg_tokens = (
            self.total_tokens / self.request_count 
            if self.request_count > 0 else 0.0
        )
        
        return {
            'name': self.name,
            'provider_id': self.provider_id,
            'created_at': self.created_at.isoformat(),
            'request_count': self.request_count,
            'total_tokens': self.total_tokens,
            'total_latency': self.total_latency,
            'average_latency': avg_latency,
            'average_tokens': avg_tokens
        }
    
    def __str__(self) -> str:
        return f"{self.name}(id={self.provider_id[:8]}, requests={self.request_count})"
    
    def __repr__(self) -> str:
        return self.__str__()


class LLMError(Exception):
    """LLM相关错误"""
    
    def __init__(self, message: str, provider: str = "", model_id: str = "", error_code: str = ""):
        super().__init__(message)
        self.provider = provider
        self.model_id = model_id
        self.error_code = error_code
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'message': str(self),
            'provider': self.provider,
            'model_id': self.model_id,
            'error_code': self.error_code,
            'timestamp': self.timestamp.isoformat()
        }


class ModelNotFoundError(LLMError):
    """模型未找到错误"""
    pass


class ProviderUnavailableError(LLMError):
    """提供者不可用错误"""
    pass


class RateLimitError(LLMError):
    """速率限制错误"""
    pass


class TokenLimitError(LLMError):
    """Token限制错误"""
    pass


class AuthenticationError(LLMError):
    """认证错误"""
    pass


class QuotaExceededError(LLMError):
    """配额超限错误"""
    pass