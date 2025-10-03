#!/usr/bin/env python3
"""
LLM抽象层模块初始化文件
导出统一的LLM接口和实现

运行环境: Python 3.11+
依赖: typing, asyncio
"""

# 基础接口和数据类
from .base import (
    BaseLLMProvider,
    ModelType,
    ProviderType,
    ModelInfo,
    LLMRequest,
    LLMResponse,
    StreamChunk,
    TokenUsage,
    LLMError,
    ModelNotFoundError,
    ProviderUnavailableError,
    RateLimitError,
    AuthenticationError,
    QuotaExceededError
)

# 具体提供商实现
from .providers import (
    OpenAIProvider,
    AnthropicProvider,
    GoogleProvider,
    LocalProvider
)

# LLM管理器
from .manager import (
    LLMManager,
    LoadBalanceStrategy
)

# 模块信息
__version__ = "1.0.0"
__author__ = "Shrimp Agent Team"
__description__ = "LLM抽象层 - 统一多提供商接口"

# 导出列表
__all__ = [
    # 基础接口
    "BaseLLMProvider",
    "ModelType",
    "ProviderType",
    "ModelInfo",
    "LLMRequest",
    "LLMResponse",
    "StreamChunk",
    "TokenUsage",
    
    # 异常类
    "LLMError",
    "ModelNotFoundError",
    "ProviderUnavailableError",
    "RateLimitError",
    "AuthenticationError",
    "QuotaExceededError",
    
    # 提供商实现
    "OpenAIProvider",
    "AnthropicProvider",
    "GoogleProvider",
    "LocalProvider",
    
    # 管理器
    "LLMManager",
    "LoadBalanceStrategy"
]


def create_llm_manager(config: dict) -> LLMManager:
    """创建LLM管理器的工厂函数
    
    Args:
        config: LLM配置
        
    Returns:
        LLM管理器实例
        
    Example:
        >>> config = {
        ...     'providers': {
        ...         'openai': {
        ...             'enabled': True,
        ...             'api_key': 'your-api-key'
        ...         },
        ...         'anthropic': {
        ...             'enabled': True,
        ...             'api_key': 'your-api-key'
        ...         }
        ...     },
        ...     'load_balance_strategy': 'round_robin',
        ...     'enable_fallback': True
        ... }
        >>> manager = create_llm_manager(config)
    """
    return LLMManager(config)


def get_default_config() -> dict:
    """获取默认配置
    
    Returns:
        默认LLM配置
    """
    return {
        'providers': {
            'openai': {
                'enabled': False,
                'api_key': '',
                'base_url': 'https://api.openai.com/v1',
                'organization': ''
            },
            'anthropic': {
                'enabled': False,
                'api_key': '',
                'base_url': 'https://api.anthropic.com'
            },
            'google': {
                'enabled': False,
                'api_key': '',
                'base_url': 'https://generativelanguage.googleapis.com'
            },
            'local': {
                'enabled': False,
                'base_url': 'http://localhost:8000',
                'model_path': ''
            }
        },
        'load_balance_strategy': 'round_robin',
        'enable_fallback': True,
        'max_retries': 3,
        'timeout': 30.0
    }


def validate_config(config: dict) -> tuple[bool, list[str]]:
    """验证LLM配置
    
    Args:
        config: 待验证的配置
        
    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []
    
    # 检查必需字段
    if 'providers' not in config:
        errors.append("缺少 'providers' 配置")
        return False, errors
    
    providers = config['providers']
    enabled_providers = [name for name, cfg in providers.items() if cfg.get('enabled', False)]
    
    if not enabled_providers:
        errors.append("至少需要启用一个LLM提供商")
    
    # 验证各提供商配置
    for provider_name, provider_config in providers.items():
        if not provider_config.get('enabled', False):
            continue
        
        if provider_name in ['openai', 'anthropic', 'google']:
            if not provider_config.get('api_key'):
                errors.append(f"{provider_name} 提供商缺少 API key")
        
        elif provider_name == 'local':
            if not provider_config.get('base_url'):
                errors.append("本地提供商缺少 base_url")
    
    # 验证负载均衡策略
    strategy = config.get('load_balance_strategy', 'round_robin')
    valid_strategies = ['round_robin', 'random', 'least_loaded', 'fastest', 'cheapest']
    if strategy not in valid_strategies:
        errors.append(f"无效的负载均衡策略: {strategy}")
    
    return len(errors) == 0, errors